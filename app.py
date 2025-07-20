import os
import sys
import shutil
import json
import re
import platform
from datetime import datetime, timedelta
from calendar import monthrange
import pytz
from flask import Flask, request, jsonify, render_template, url_for, send_file, redirect, session, flash
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import pandas as pd
from werkzeug.security import generate_password_hash

# 导入安全组件
from security_constants import ALLOWED_GRADES, PERIOD_CONSTANTS, USER_ROLES, SCORE_VALIDATION
from input_validator import InputValidator, SQLSafetyHelper
from security_middleware import security_middleware

def validate_grade_input(grade):
    """验证年级输入，防止SQL注入"""
    return InputValidator.validate_grade(grade)

def sanitize_teacher_grade(teacher_grade):
    """清理教师年级输入"""
    if not teacher_grade or not InputValidator.validate_grade(teacher_grade):
        return None
    return teacher_grade


from db import get_conn, put_conn
from models import User, Score
from forms import LoginForm, RegistrationForm, ScoreForm
from period_utils import get_current_semester_config, calculate_period_info

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
CORS(app)

# Flask-Login配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录后再访问此页面'

@login_manager.user_loader
def load_user(user_id):
    conn = get_conn()
    try:
        user = User.get_user_by_id(int(user_id), conn)
        return user
    finally:
        put_conn(conn)

# 导出目录配置
EXPORT_FOLDER = os.getenv("EXPORT_FOLDER", "exports")
os.makedirs(EXPORT_FOLDER, exist_ok=True)

@app.route('/health')
def health_check():
    """健康检查端点，用于 Render 等平台检测服务状态"""
    try:
        # 简单的数据库连接测试
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        put_conn(conn)
        return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # 教师用户重定向到管理面板，不能评分
    if current_user.is_teacher():
        return redirect(url_for('admin'))
    
    # 根据用户班级自动确定应该评价的年级
    def get_target_grade(user_class):
        """根据评分链条确定目标年级：中预→初一→初二→中预, 高一↔高二, 高一VCE↔高二VCE"""
        if not user_class:
            return None
            
        user_class = user_class.strip()
        
        # 判断用户年级
        if user_class.startswith('中预'):
            return '初一'  # 中预评初一
        elif user_class.startswith('初一'):
            return '初二'  # 初一评初二
        elif user_class.startswith('初二'):
            return '中预'  # 初二评中预
        elif user_class.startswith('高一') and 'VCE' in user_class:
            return '高二VCE'  # 高一VCE评高二VCE
        elif user_class.startswith('高二') and 'VCE' in user_class:
            return '高一VCE'  # 高二VCE评高一VCE
        elif user_class.startswith('高一'):
            return '高二'  # 高一评高二
        elif user_class.startswith('高二'):
            return '高一'  # 高二评高一
        else:
            return None
    
    target_grade = get_target_grade(current_user.class_name)
    
    # 获取当前周期信息
    try:
        config_data = get_current_semester_config()
        if config_data:
            period_info = calculate_period_info(semester_config=config_data['semester'])
            current_period = {
                'number': period_info['period_number'] + 1,
                'start': period_info['period_start'].strftime('%Y-%m-%d'),
                'end': period_info['period_end'].strftime('%Y-%m-%d')
            }
        else:
            current_period = None
    except Exception as e:
        print(f"Error: {e}")
        current_period = None
    
    return render_template('index.html', 
                          user=current_user, 
                          auto_target_grade=target_grade,
                          current_period=current_period)

@app.route('/login', methods=['GET', 'POST'])
@security_middleware.rate_limit(max_requests=50, window=300)  # 5分钟最多50次尝试（开发友好）
@security_middleware.login_protection
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        conn = get_conn()
        try:
            user = User.get_user_by_username(form.username.data, conn)
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('用户名或密码错误', 'error')
        finally:
            put_conn(conn)
    
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    """管理员用户管理 - 只有管理员可以管理用户"""
    if not current_user.is_admin():
        return "权限不足，只有管理员可以管理用户", 403
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Handle AJAX requests
        if request.method == 'POST' and request.is_json:
            data = request.get_json()
            action = data.get('action')
            
            if action == 'delete':
                user_id = data.get('user_id')
                if user_id == current_user.id:
                    return jsonify(success=False, message='不能删除自己的账户')
                
                cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
                if cur.rowcount > 0:
                    conn.commit()
                    return jsonify(success=True, message='用户删除成功')
                else:
                    return jsonify(success=False, message='用户不存在')
            
            elif action == 'bulk_delete':
                user_ids = data.get('user_ids', [])
                if current_user.id in user_ids:
                    return jsonify(success=False, message='不能删除自己的账户')
                
                placeholders = ','.join(['?' for _ in user_ids])
                cur.execute(f"DELETE FROM users WHERE id IN ({placeholders})", user_ids)
                deleted_count = cur.rowcount
                conn.commit()
                return jsonify(success=True, message=f'成功删除{deleted_count}个用户')
            
            elif action == 'create':
                username = data.get('username')
                password = data.get('password')
                class_name = data.get('class_name')
                role = data.get('role', 'student')
                
                if not all([username, password, class_name]):
                    return jsonify(success=False, message='缺少必要信息')
                
                cur.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cur.fetchone():
                    return jsonify(success=False, message='用户名已存在')
                
                password_hash = generate_password_hash(password)
                cur.execute("""
                    INSERT INTO users (username, password_hash, role, class_name)
                    VALUES (?, ?, ?, ?)
                """, (username, password_hash, role, class_name))
                conn.commit()
                return jsonify(success=True, message=f'用户 {username} 创建成功')
        
        elif request.method == 'POST':
            # Handle form submission
            username = request.form.get('username')
            password = request.form.get('password')
            class_name = request.form.get('class_name')
            role = request.form.get('role', 'student')
            
            if username and password and class_name:
                cur.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cur.fetchone():
                    flash('用户名已存在', 'error')
                else:
                    password_hash = generate_password_hash(password)
                    cur.execute("""
                        INSERT INTO users (username, password_hash, role, class_name)
                        VALUES (?, ?, ?, ?)
                    """, (username, password_hash, role, class_name))
                    conn.commit()
                    flash(f'用户 {username} 创建成功', 'success')
        
        # 查看所有用户及评分统计 - 教师按用户名智能排序
        cur.execute('''
            SELECT u.id, u.username, u.class_name, u.role, u.created_at,
                   COALESCE(sc.score_count, 0) as score_count
            FROM users u
            LEFT JOIN (
                SELECT user_id, COUNT(*) as score_count
                FROM scores
                GROUP BY user_id
            ) sc ON u.id = sc.user_id
            ORDER BY 
                CASE u.role 
                    WHEN 'admin' THEN 1 
                    WHEN 'student' THEN 2 
                    WHEN 'teacher' THEN 3 
                    ELSE 4 
                END,
                -- 教师按用户名智能排序：t+数字的按数字排序，其他按字母排序
                CASE 
                    WHEN u.role = 'teacher' AND u.username LIKE 't%' AND u.username GLOB 't[0-9]*' THEN 
                        CAST(SUBSTR(u.username, 2) AS INTEGER)
                    WHEN u.role = 'teacher' THEN 999
                    ELSE 0
                END,
                u.class_name,
                u.username
        ''')
        users = cur.fetchall()
        return render_template('admin_users.html', users=users, user=current_user)
        
    finally:
        put_conn(conn)

@app.route('/api/semester_config')
@login_required
def api_semester_config():
    """获取当前学期配置和班级列表"""
    try:
        config_data = get_current_semester_config()
        if not config_data:
            return jsonify(success=False, message='未找到学期配置')
        
        semester = config_data['semester']
        classes = config_data['classes']
        
        # 按年级分组班级
        classes_by_grade = {}
        for class_info in classes:
            grade = class_info['grade_name']
            if grade not in classes_by_grade:
                classes_by_grade[grade] = []
            classes_by_grade[grade].append(class_info['class_name'])
        
        # 计算当前周期信息
        period_info = calculate_period_info(semester_config=semester)
        
        return jsonify(
            success=True,
            semester={
                'name': semester['semester_name'],
                'start_date': semester['start_date'],
                'first_period_end': semester['first_period_end_date']
            },
            classes=classes_by_grade,
            current_period={
                'number': period_info['period_number'] + 1,  # 显示时从1开始
                'start': period_info['period_start'].strftime('%Y-%m-%d'),
                'end': period_info['period_end'].strftime('%Y-%m-%d')
            }
        )
    except Exception as e:
        return jsonify(success=False, message=f'获取配置失败: {str(e)}')

@app.route('/admin/semester', methods=['GET', 'POST'])
@login_required
def admin_semester():
    """管理员学期设置 - 只有管理员可以设置学期"""
    if not current_user.is_admin():
        return "权限不足，只有管理员可以设置学期", 403
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        if request.method == 'POST':
            # 处理文件下载请求（表单提交）
            if request.form.get('json_data'):
                try:
                    data = json.loads(request.form.get('json_data'))
                    action = data.get('action')
                    
                    if action == 'export_backup':
                        # 数据备份功能
                        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
                        backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
                        
                        if db_url.startswith('sqlite'):
                            # SQLite 文件备份
                            backup_filename = f'semester_backup_{backup_time}.db'
                            backup_path = os.path.join(EXPORT_FOLDER, backup_filename)
                            
                            # 确保exports目录存在
                            os.makedirs(EXPORT_FOLDER, exist_ok=True)
                            
                            # 复制数据库文件（仅限 SQLite）
                            import re
                            db_filename = re.search(r'sqlite:///(.+)', db_url).group(1)
                            if not os.path.isabs(db_filename):
                                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_filename)
                            else:
                                db_path = db_filename
                            
                            shutil.copy2(db_path, backup_path)
                            
                            # 直接返回文件下载
                            return send_file(backup_path, as_attachment=True, download_name=backup_filename)
                        
                        else:
                            # PostgreSQL 逻辑备份（导出为 SQL）
                            backup_filename = f'semester_backup_{backup_time}.sql'
                            backup_path = os.path.join(EXPORT_FOLDER, backup_filename)
                            
                            # 确保exports目录存在
                            os.makedirs(EXPORT_FOLDER, exist_ok=True)
                            
                            try:
                                # 生成 SQL 备份
                                conn = get_conn()
                                cur = conn.cursor()
                                
                                with open(backup_path, 'w', encoding='utf-8') as f:
                                    f.write("-- ClassComp Score 数据备份\n")
                                    f.write(f"-- 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                                    
                                    # 备份用户表
                                    f.write("-- 用户数据\n")
                                    cur.execute("SELECT * FROM users ORDER BY id")
                                    users = cur.fetchall()
                                    for user in users:
                                        f.write(f"INSERT INTO users (id, username, password_hash, role, class_name, created_at) VALUES ")
                                        f.write(f"({user['id']}, '{user['username']}', '{user['password_hash']}', ")
                                        f.write(f"'{user['role']}', '{user['class_name']}', '{user['created_at']}');\n")
                                    
                                    f.write("\n-- 评分数据\n")
                                    cur.execute("SELECT * FROM scores ORDER BY id")
                                    scores = cur.fetchall()
                                    for score in scores:
                                        f.write(f"INSERT INTO scores (id, user_id, evaluator_name, evaluator_class, ")
                                        f.write(f"target_grade, target_class, score1, score2, score3, total, note, created_at) VALUES ")
                                        f.write(f"({score['id']}, {score['user_id']}, '{score['evaluator_name']}', ")
                                        f.write(f"'{score['evaluator_class']}', '{score['target_grade']}', '{score['target_class']}', ")
                                        f.write(f"{score['score1']}, {score['score2']}, {score['score3']}, {score['total']}, ")
                                        f.write(f"'{score['note']}', '{score['created_at']}');\n")
                                    
                                    # 备份学期配置
                                    f.write("\n-- 学期配置\n")
                                    cur.execute("SELECT * FROM semester_config ORDER BY id")
                                    semesters = cur.fetchall()
                                    for semester in semesters:
                                        f.write(f"INSERT INTO semester_config (id, semester_name, start_date, end_date, ")
                                        f.write(f"first_period_end_date, is_active, created_at, updated_at) VALUES ")
                                        f.write(f"({semester['id']}, '{semester['semester_name']}', '{semester['start_date']}', ")
                                        f.write(f"'{semester['end_date']}', '{semester['first_period_end_date']}', ")
                                        f.write(f"{semester['is_active']}, '{semester['created_at']}', '{semester['updated_at']}');\n")
                                
                                put_conn(conn)
                                
                                # 返回 SQL 文件下载
                                return send_file(backup_path, as_attachment=True, download_name=backup_filename)
                                
                            except Exception as e:
                                return f"PostgreSQL 备份失败：{str(e)}", 500
                except Exception as e:
                    return f"备份失败：{str(e)}", 500
            
            # 处理JSON请求
            elif request.is_json:
                data = request.get_json()
                action = data.get('action')
                
                if action == 'update_config':
                    # 更新学期基本配置
                    semester_name = data.get('semester_name')
                    start_date = data.get('start_date')
                    first_period_end_date = data.get('first_period_end_date')
                    
                    if not all([semester_name, start_date, first_period_end_date]):
                        return jsonify(success=False, message='缺少必要信息')
                    
                    # 查找活跃学期
                    cur.execute('SELECT id FROM semester_config WHERE is_active = 1')
                    semester = cur.fetchone()
                    
                    if semester:
                        # 更新现有的活跃学期
                        cur.execute('''
                            UPDATE semester_config 
                            SET semester_name = ?, start_date = ?, first_period_end_date = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (semester_name, start_date, first_period_end_date, semester['id']))
                        conn.commit()
                        return jsonify(success=True, message='学期配置更新成功')
                    else:
                        # 没有活跃学期，创建新的学期配置
                        cur.execute('''
                            INSERT INTO semester_config (semester_name, start_date, first_period_end_date, is_active)
                            VALUES (?, ?, ?, 1)
                        ''', (semester_name, start_date, first_period_end_date))
                        conn.commit()
                        return jsonify(success=True, message='新学期配置创建成功')
                
                elif action == 'update_classes':
                    # 更新班级配置 - 使用原子操作防止重复
                    classes = data.get('classes', [])
                    
                    # 使用事务确保原子性
                    conn.execute('BEGIN IMMEDIATE')
                    try:
                        # 获取当前学期ID，如果没有则创建默认学期
                        cur.execute('SELECT id FROM semester_config WHERE is_active = 1')
                        semester = cur.fetchone()
                        
                        if not semester:
                            # 没有活跃学期，先创建一个简单的默认学期配置
                            current_date = datetime.now()
                            
                            # 简单的默认：第一期结束日期设为今天+PERIOD_DAYS后的星期日
                            default_end = current_date + timedelta(days=PERIOD_CONSTANTS['DAYS_IN_PERIOD'])
                            
                            # 找到该日期之后的第一个星期日
                            days_until_sunday = (PERIOD_CONSTANTS['SUNDAY_WEEKDAY'] - default_end.weekday()) % 7
                            if days_until_sunday == 0 and default_end.weekday() != PERIOD_CONSTANTS['SUNDAY_WEEKDAY']:
                                days_until_sunday = 7
                            first_period_end = default_end + timedelta(days=days_until_sunday)
                            
                            semester_name = f'{current_date.year}年学期-默认配置'
                            start_date = current_date.strftime('%Y-%m-%d')
                            first_period_end_date = first_period_end.strftime('%Y-%m-%d')
                            
                            cur.execute('''
                                INSERT INTO semester_config (semester_name, start_date, first_period_end_date, is_active)
                                VALUES (?, ?, ?, 1)
                            ''', (semester_name, start_date, first_period_end_date))
                            semester_id = cur.lastrowid
                            print(f"创建默认学期: {semester_name}, 开始: {start_date}, 第一期结束: {first_period_end_date}")
                        else:
                            semester_id = semester['id']
                        
                        # 先将所有班级设为不活跃
                        cur.execute('UPDATE semester_classes SET is_active = 0 WHERE semester_id = ?', (semester_id,))
                        
                        # 使用UPSERT模式更新班级配置
                        for class_info in classes:
                            grade_name = class_info.get('grade_name')
                            class_name = class_info.get('class_name')
                            
                            if not grade_name or not class_name:
                                continue
                            
                            # 使用INSERT OR REPLACE确保原子性和唯一性
                            cur.execute('''
                                INSERT OR REPLACE INTO semester_classes 
                                (semester_id, grade_name, class_name, is_active, created_at, updated_at)
                                SELECT ?, ?, ?, 1, 
                                       COALESCE((SELECT created_at FROM semester_classes 
                                               WHERE semester_id = ? AND class_name = ?), CURRENT_TIMESTAMP),
                                       CURRENT_TIMESTAMP
                            ''', (semester_id, grade_name, class_name, semester_id, class_name))
                        
                        conn.commit()
                        return jsonify(success=True, message=f'班级配置更新成功，共{len(classes)}个班级')
                        
                    except Exception as e:
                        conn.rollback()
                        return jsonify(success=False, message=f'班级配置更新失败: {str(e)}')
                
                elif action == 'reset_database':
                    # 重置数据库（慎用）
                    confirm_code = data.get('confirm_code')
                    if confirm_code != 'RESET_CONFIRM':
                        return jsonify(success=False, message='确认码错误')
                    
                    try:
                        # 清空评分数据
                        cur.execute('DELETE FROM scores')
                        cur.execute('DELETE FROM scores_history')
                        
                        # 重置学期配置
                        cur.execute('UPDATE semester_config SET is_active = 0')
                        
                        conn.commit()
                        return jsonify(success=True, message='数据库重置成功，请重新配置学期')
                    except Exception as e:
                        return jsonify(success=False, message=f'重置失败: {str(e)}')
        
        # GET请求：获取当前学期配置
        cur.execute('''
            SELECT * FROM semester_config WHERE is_active = 1
        ''')
        semester = cur.fetchone()
        
        if semester:
            # 获取班级配置，按正确的年级顺序排列
            cur.execute('''
                SELECT grade_name, class_name
                FROM semester_classes 
                WHERE semester_id = ? AND is_active = 1
                ORDER BY 
                    CASE grade_name 
                        WHEN '中预' THEN 1 
                        WHEN '初一' THEN 2 
                        WHEN '初二' THEN 3 
                        WHEN '高一' THEN 4 
                        WHEN '高二' THEN 5 
                        WHEN '高一VCE' THEN 6 
                        WHEN '高二VCE' THEN 7 
                        ELSE 8 
                    END, 
                    class_name
            ''', (semester['id'],))
            classes = cur.fetchall()
        else:
            classes = []
        
        return render_template('admin_semester.html', 
                             semester=semester, 
                             classes=classes, 
                             user=current_user)
        
    finally:
        put_conn(conn)

@app.route('/submit_scores', methods=['POST'])
@login_required
@security_middleware.rate_limit(max_requests=100, window=60)  # 1分钟最多100次提交（开发友好）
def submit_scores():
    # 教师不能提交评分
    if current_user.is_teacher():
        return jsonify(success=False, message="教师用户无权限提交评分"), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, message="无效的请求数据"), 400
        
        # 验证必填字段
        required_fields = ["target_grade", "scores"]
        if not all(field in data for field in required_fields):
            security_middleware.log_security_event("INVALID_INPUT", "缺少必要字段")
            return jsonify(success=False, message="缺少必要字段"), 400
        
        # 验证年级输入
        if not InputValidator.validate_grade(data["target_grade"]):
            security_middleware.log_security_event("INVALID_GRADE", f"无效年级: {data.get('target_grade')}")
            return jsonify(success=False, message="无效的年级"), 400
        
        conn = get_conn()
        
        try:
            # 批量插入评分
            inserted_count = 0
            total_overwrite_count = 0
            errors = []
            for score_data in data["scores"]:
                try:
                    # 验证分数
                    score1 = int(score_data["score1"])
                    score2 = int(score_data["score2"])
                    score3 = int(score_data["score3"])
                    
                    if not all(InputValidator.validate_score(s) for s in [score1, score2, score3]):
                        errors.append("分数必须在0-10之间")
                        continue
                    
                    # 验证班级名称
                    class_name = score_data.get("className", "")
                    if not InputValidator.validate_class_name(class_name):
                        errors.append(f"无效的班级名称: {class_name}")
                        continue
                    
                    # 清理备注
                    note = InputValidator.sanitize_text(score_data.get("note", ""), max_length=200)
                    
                    score_id, error, overwrite_count = Score.create_score(
                        user_id=current_user.id,
                        evaluator_name=current_user.username,
                        evaluator_class=current_user.class_name,
                        target_grade=data["target_grade"],
                        target_class=class_name,
                        score1=score1,
                        score2=score2,
                        score3=score3,
                        note=note,
                        conn=conn
                    )
                    
                    if score_id:
                        inserted_count += 1
                        total_overwrite_count += overwrite_count
                    else:
                        errors.append(error)
                        
                except ValueError as e:
                    errors.append(f"分数格式错误: {e}")
                except KeyError as e:
                    errors.append(f"缺少必要字段: {e}")
                except Exception as e:
                    errors.append(f"系统错误: {str(e)}")
            
            if inserted_count > 0:
                # 构建成功消息
                success_msg = f"成功提交{inserted_count}条评分记录"
                if total_overwrite_count > 0:
                    success_msg += f"，覆盖了{total_overwrite_count}条同周期记录"
                
                if errors:
                    return jsonify(success=True, message=f"{success_msg}，{len(errors)}条失败", errors=errors)
                else:
                    return jsonify(success=True, message=success_msg)
            else:
                if errors:
                    return jsonify(success=False, message="评分提交失败", errors=errors)
                else:
                    return jsonify(success=False, message="没有新的评分被提交")
                
        finally:
            put_conn(conn)
    
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/my_scores')
@login_required
def my_scores():
    """查看评分历史 - 管理员看全部，教师看本年级班级评分完成情况，学生看个人评分"""
    conn = get_conn()
    try:
        if current_user.is_admin():
            # 管理员查看所有评分
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, u.username, u.class_name as evaluator_class_name
                FROM scores s 
                JOIN users u ON s.user_id = u.id 
                ORDER BY s.created_at DESC
            ''')
            scores = cursor.fetchall()
            return render_template('simple_my_scores.html', scores=scores, user=current_user)
        elif current_user.is_teacher():
            # 教师查看本年级班级本周期评分完成情况
            # 使用学期配置计算当前周期
            config_data = get_current_semester_config(conn)
            if config_data:
                period_info = calculate_period_info(semester_config=config_data['semester'])
            else:
                # 回退到默认逻辑
                period_info = calculate_period_info()
            
            period_start = period_info['period_start']
            period_end = period_info['period_end']
            period_number = period_info['period_number']
            
            if current_user.class_name and ('全校' in current_user.class_name or 'ALL' in current_user.class_name.upper()):
                # 全校数据教师看所有年级班级的本周期评分完成情况
                # 修复：基于学期配置中的活跃班级，而不是用户表中的所有班级
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT 
                        sc.class_name,
                        CASE WHEN COUNT(s.id) > 0 THEN 1 ELSE 0 END as has_scored_this_period,
                        COUNT(s.id) as score_count_this_period,
                        MAX(s.created_at) as latest_score_time
                    FROM semester_classes sc
                    LEFT JOIN users u ON sc.class_name = u.class_name AND u.role = 'student'
                    LEFT JOIN scores s ON u.id = s.user_id 
                        AND DATE(s.created_at) >= ? 
                        AND DATE(s.created_at) <= ?
                    WHERE sc.is_active = 1 AND sc.semester_id = (SELECT id FROM semester_config WHERE is_active = 1)
                    GROUP BY sc.class_name, sc.grade_name
                    ORDER BY 
                        CASE sc.grade_name 
                            WHEN '中预' THEN 1 
                            WHEN '初一' THEN 2 
                            WHEN '初二' THEN 3 
                            WHEN '高一' THEN 4 
                            WHEN '高二' THEN 5 
                            WHEN '高一VCE' THEN 6 
                            WHEN '高二VCE' THEN 7 
                            ELSE 8 
                        END, 
                        sc.class_name
                ''', (period_start.strftime('%Y-%m-%d'), period_end.strftime('%Y-%m-%d')))
                class_status = cursor.fetchall()
                return render_template('teacher_monitoring.html', 
                                     class_status=class_status, 
                                     user=current_user, 
                                     is_school_wide=True,
                                     current_period=period_number + 1,
                                     period_start=period_start,
                                     period_end=period_end)
            else:
                # 普通教师查看本年级班级本周期评分完成情况
                teacher_grade = None
                if current_user.class_name:
                    class_name = current_user.class_name.lower()
                    if 't6' in class_name or '中预' in class_name:
                        teacher_grade = '中预'
                    elif 't7' in class_name or '初一' in class_name:
                        teacher_grade = '初一'
                    elif 't8' in class_name or '初二' in class_name:
                        teacher_grade = '初二'
                    elif 't10' in class_name or '高一' in class_name:
                        teacher_grade = '高一'
                    elif 't11' in class_name or '高二' in class_name:
                        teacher_grade = '高二'
                
                if not teacher_grade:
                    return f"无法确定教师所属年级，当前班级：{current_user.class_name}", 400
                
                # 高一高二教师需要包含对应的VCE班级
                if teacher_grade in ['高一', '高二']:
                    teacher_grades = [teacher_grade, f'{teacher_grade}VCE']
                else:
                    teacher_grades = [teacher_grade]
                
                cursor = conn.cursor()
                # 构建IN查询条件
                grade_placeholders = ','.join(['?' for _ in teacher_grades])
                cursor.execute(f'''
                    SELECT DISTINCT 
                        sc.class_name,
                        CASE WHEN COUNT(s.id) > 0 THEN 1 ELSE 0 END as has_scored_this_period,
                        COUNT(s.id) as score_count_this_period,
                        MAX(s.created_at) as latest_score_time
                    FROM semester_classes sc
                    LEFT JOIN users u ON sc.class_name = u.class_name AND u.role = 'student'
                    LEFT JOIN scores s ON u.id = s.user_id 
                        AND DATE(s.created_at) >= ? 
                        AND DATE(s.created_at) <= ?
                    WHERE sc.is_active = 1 
                        AND sc.semester_id = (SELECT id FROM semester_config WHERE is_active = 1)
                        AND sc.grade_name IN ({grade_placeholders})
                    GROUP BY sc.class_name, sc.grade_name
                    ORDER BY 
                        CASE sc.grade_name 
                            WHEN '中预' THEN 1 
                            WHEN '初一' THEN 2 
                            WHEN '初二' THEN 3 
                            WHEN '高一' THEN 4 
                            WHEN '高二' THEN 5 
                            WHEN '高一VCE' THEN 6 
                            WHEN '高二VCE' THEN 7 
                            ELSE 8 
                        END, 
                        sc.class_name
                ''', [period_start.strftime('%Y-%m-%d'), period_end.strftime('%Y-%m-%d')] + teacher_grades)
                class_status = cursor.fetchall()
                return render_template('teacher_monitoring.html', 
                                     class_status=class_status, 
                                     user=current_user, 
                                     is_school_wide=False, 
                                     teacher_grade=teacher_grade,
                                     current_period=period_number + 1,
                                     period_start=period_start,
                                     period_end=period_end)
        else:
            # 普通学生只看个人评分
            scores = Score.get_user_scores(current_user.id, conn)
            return render_template('simple_my_scores.html', scores=scores, user=current_user)
    finally:
        put_conn(conn)

@app.route('/api/my_scores')
@login_required
def api_my_scores():
    """获取个人评分历史API"""
    conn = get_conn()
    try:
        limit = request.args.get('limit', 50, type=int)
        scores = Score.get_user_scores(current_user.id, conn, limit)
        
        # 转换为JSON格式
        score_list = []
        for score in scores:
            # Handle both datetime objects and string formats
            created_at = score['created_at']
            if hasattr(created_at, 'strftime'):
                created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                created_str = str(created_at)
                
            score_list.append({
                'id': score['id'],
                'evaluator_class': score['evaluator_class'],
                'target_grade': score['target_grade'],
                'target_class': score['target_class'],
                'score1': score['score1'],
                'score2': score['score2'],
                'score3': score['score3'],
                'total': score['total'],
                'note': score['note'],
                'created_at': created_str
            })
        
        return jsonify(success=True, scores=score_list)
    finally:
        put_conn(conn)

@app.route('/export_excel')
@login_required
def export_excel():
    """导出Excel报告 - 支持月度报告和全部数据导出"""
    if not (current_user.is_admin() or current_user.is_teacher()):
        return "权限不足", 403
    
    month = request.args.get("month")
    all_data = request.args.get("all_data", "false").lower() == "true"  # 是否导出全部数据
    
    if not all_data and not month:
        return "请提供 month=YYYY-MM 查询参数或 all_data=true 参数", 400
    
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        import os
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        # 教师权限控制 - 普通教师只能导出本年级数据，全校数据教师可以导出所有数据
        teacher_grade_filter = ""
        if current_user.is_teacher():
            # 检查是否是全校数据教师
            if current_user.class_name and ('全校' in current_user.class_name or 'ALL' in current_user.class_name.upper()):
                # 全校数据教师可以导出所有数据
                teacher_grade_filter = ""
            else:
                # 普通教师只能导出本年级数据
                teacher_grade = None
                if current_user.class_name:
                    class_name = current_user.class_name.lower()
                    if 't6' in class_name or '中预' in class_name:
                        teacher_grade = '中预'
                    elif 't7' in class_name or '初一' in class_name:
                        teacher_grade = '初一'
                    elif 't8' in class_name or '初二' in class_name:
                        teacher_grade = '初二'
                    elif 't10' in class_name or '高一' in class_name:
                        teacher_grade = '高一'
                    elif 't11' in class_name or '高二' in class_name:
                        teacher_grade = '高二'
                
                if not teacher_grade:
                    return f"无法确定教师所属年级，当前班级：{current_user.class_name}", 400
                
                # 高一高二教师需要包含对应的VCE班级数据
                if teacher_grade in ['高一', '高二']:
                    teacher_grade_filter = " AND (target_grade LIKE ? OR target_grade LIKE ?)"
                    teacher_grade_params = [f'%{teacher_grade}%', f'%{teacher_grade}VCE%']
                else:
                    teacher_grade_filter = " AND target_grade LIKE ?"
                    teacher_grade_params = [f'%{teacher_grade}%']
        
        # 构建SQL查询 - 根据是否导出全部数据来决定时间条件
        if all_data:
            # 导出全部数据 - 不添加时间条件
            time_condition = ""
            query_params = []
        else:
            # 导出特定月份数据
            if is_sqlite:
                time_condition = f"WHERE strftime('%Y-%m', created_at) = {placeholder}"
            else:
                time_condition = f"WHERE to_char(created_at, 'YYYY-MM') = {placeholder}"
            query_params = [month]
        
        if is_sqlite:
            sql = f"""
                SELECT
                  id,
                  evaluator_name,
                  evaluator_class,
                  target_grade,
                  target_class,
                  score1,
                  score2,
                  score3,
                  total,
                  note,
                  created_at
                FROM scores
                {time_condition}{teacher_grade_filter}
                ORDER BY target_grade, target_class, evaluator_class, created_at
            """
        else:
            sql = f"""
                SELECT
                  id,
                  evaluator_name,
                  evaluator_class,
                  target_grade,
                  target_class,
                  score1,
                  score2,
                  score3,
                  total,
                  note,
                  created_at
                FROM scores
                {time_condition}{teacher_grade_filter}
                ORDER BY created_at
            """
        
        # 构建完整的查询参数
        if teacher_grade_filter and 'teacher_grade_params' in locals():
            final_params = query_params + teacher_grade_params
        else:
            final_params = query_params if query_params else []
        
        if final_params:
            cur.execute(sql, final_params)
        else:
            cur.execute(sql)
        rows = cur.fetchall()
        # 不要在这里关闭连接，后面还需要查询历史记录
        # put_conn(conn)
        
        if not rows:
            put_conn(conn)  # 提前返回时关闭连接
            data_type = "全部数据" if all_data else "当月数据"
            return f"无{data_type}", 200
            
        df = pd.DataFrame(rows, columns=[
            'id', 'evaluator_name', 'evaluator_class', 'target_grade', 
            'target_class', 'score1', 'score2', 'score3', 'total', 
            'note', 'created_at'
        ])
        
        data_type = "全部数据" if all_data else f"{month}月数据"
        print(f"📊 导出前{data_type}总数: {len(df)}")
        
        # 增强时间处理逻辑
        def parse_datetime_robust(dt_str):
            """强力解析各种时间格式"""
            if pd.isna(dt_str):
                return None
            
            dt_str = str(dt_str).strip()
            
            # 处理带时区的格式
            if '+' in dt_str:
                dt_str = dt_str.split('+')[0]
            if 'T' in dt_str:
                dt_str = dt_str.replace('T', ' ')
            
            # 尝试解析
            try:
                return pd.to_datetime(dt_str)
            except Exception as e:
                print(f"Error: {e}")
                try:
                    # 如果失败，尝试只取日期部分
                    date_part = dt_str.split()[0]
                    return pd.to_datetime(date_part)
                except Exception as parse_error:
                    print(f"⚠️ 无法解析时间: {dt_str}, 错误: {parse_error}")
                    return None
        
        df["created_at"] = df["created_at"].apply(parse_datetime_robust)
        df = df.dropna(subset=['created_at'])
        
        print(f"📊 时间解析后数据: {len(df)}")
        
        # 排除测试数据（可选）
        exclude_test = request.args.get("exclude_test", "true").lower() == "true"
        if exclude_test:
            test_keywords = ['测试', 'test', 'Test', 'TEST']
            before_filter = len(df)
            for keyword in test_keywords:
                df = df[~df['evaluator_name'].str.contains(keyword, na=False)]
                df = df[~df['evaluator_class'].str.contains(keyword, na=False)]
            print(f"📊 排除测试数据后: {len(df)} (原{before_filter}条)")
        
        if df.empty:
            print("❌ 时间解析后无数据")
            put_conn(conn)
            return "时间数据解析失败，请检查数据格式", 500
            
        # 处理时区转换 - 简化处理，避免数据 loss
        df["created_at"] = pd.to_datetime(df["created_at"], errors='coerce')
        # 确保所有时间都被正确处理，无论原始格式如何
        df["created_at"] = df["created_at"].dt.tz_localize(None)
        
        # 根据导出类型生成文件名
        if all_data:
            from datetime import datetime
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"评分表_全部数据_{current_time}.xlsx"
        else:
            filename = f"评分表_{month.replace('-', '')}.xlsx"
        filepath = os.path.join(EXPORT_FOLDER, filename)
        
        try:
            with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
                print(f"开始创建Excel报表... 共{len(df)}条记录")
                
                # 计算每条记录的评分周期
                df['date_only'] = df['created_at'].dt.date
                
                # 计算每个日期所属的两周周期
                def get_biweekly_period(date):
                    # 使用学期配置计算周期
                    config_data = get_current_semester_config(conn)
                    if config_data:
                        period_info = calculate_period_info(target_date=date, semester_config=config_data['semester'])
                        return period_info['period_number'], period_info['period_end']
                    else:
                        # 回退到默认逻辑
                        period_info = calculate_period_info(target_date=date)
                        return period_info['period_number'], period_info['period_end']
                
                df['period_number'] = df['date_only'].apply(lambda x: get_biweekly_period(x)[0])
                df['period_end_date'] = df['date_only'].apply(lambda x: get_biweekly_period(x)[1])
                df['period_month'] = df['period_end_date'].apply(lambda x: x.strftime('%Y-%m'))
                
                # 只保留归属于指定月份的周期
                month_df = df[df['period_month'] == month].copy()
                
                if month_df.empty:
                    # 如果按周期归属没有数据，回退到原始的月份筛选
                    month_df = df.copy()
                    print(f"⚠️ 按周期归属无数据，使用原始月份筛选")
                
                print(f"📅 找到{len(month_df['period_number'].unique())}个评分周期的数据")
                
                # 1. 创建汇总表 - 每个周期单独一个sheet
                for period in sorted(month_df['period_number'].unique()):
                    period_df = month_df[month_df['period_number'] == period]
                    period_end = period_df['period_end_date'].iloc[0]
                    
                    # 计算每个班级在该周期内的平均分
                    period_avg = period_df.groupby(['target_grade', 'target_class'])['total'].mean().reset_index()
                    period_avg = period_avg.round(2)
                    
                    # 创建显示年级：将VCE年级合并
                    def get_display_grade(grade):
                        """将VCE年级合并为VCE显示"""
                        if 'VCE' in grade:
                            return 'VCE'
                        return grade
                    
                    period_avg['display_grade'] = period_avg['target_grade'].apply(get_display_grade)
                    
                    # 定义年级排序顺序
                    grade_order = ['中预', '初一', '初二', '高一', '高二', 'VCE']
                    
                    # 按正确的年级顺序排序
                    display_grades = sorted(
                        period_avg['display_grade'].unique(),
                        key=lambda x: grade_order.index(x) if x in grade_order else 999
                    )
                    
                    # 按显示年级分组，年级之间插入空行
                    summary_data = []
                    
                    for i, display_grade in enumerate(display_grades):
                        grade_data = period_avg[period_avg['display_grade'] == display_grade][['target_class', 'total']].copy()
                        grade_data.columns = ['被查班级', '平均分']
                        grade_data = grade_data.sort_values('被查班级')
                        
                        # 添加年级数据
                        summary_data.append(grade_data)
                        
                        # 如果不是最后一个年级，添加空行分隔
                        if i < len(display_grades) - 1:
                            empty_row = pd.DataFrame([['', '']], columns=['被查班级', '平均分'])
                            summary_data.append(empty_row)
                    
                    # 合并所有数据
                    if summary_data:
                        summary_sheet = pd.concat(summary_data, ignore_index=True)
                    else:
                        summary_sheet = pd.DataFrame(columns=['被查班级', '平均分'])
                    
                    # 创建sheet，格式：第1周期汇总
                    sheet_name = f"第{period + 1}周期汇总"
                    summary_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"✅ 创建{sheet_name}: {len(summary_sheet)}个班级")
                
                # 2. 为每个周期和年级创建评分矩阵
                for period in sorted(month_df['period_number'].unique()):
                    period_df = month_df[month_df['period_number'] == period]
                    
                    # 创建年级分组：将VCE年级合并
                    def get_matrix_grade(grade):
                        """将VCE年级合并为一个矩阵"""
                        if 'VCE' in grade:
                            return 'VCE'
                        return grade
                    
                    # 添加矩阵年级列
                    period_df_copy = period_df.copy()
                    period_df_copy['matrix_grade'] = period_df_copy['target_grade'].apply(get_matrix_grade)
                    
                    # 定义矩阵年级的排序顺序（VCE放在高二后面）
                    matrix_grade_order = ['中预', '初一', '初二', '高一', '高二', 'VCE']
                    
                    # 按正确的年级顺序处理矩阵
                    available_grades = set(period_df_copy["matrix_grade"].unique())
                    ordered_grades = [grade for grade in matrix_grade_order if grade in available_grades]
                    
                    for matrix_grade in ordered_grades:
                        grade_df = period_df_copy[period_df_copy["matrix_grade"] == matrix_grade]
                        if grade_df.empty:
                            continue
                            
                        try:
                            # 创建透视表: 被查班级 vs 评分者班级
                            pivot = grade_df.pivot_table(
                                index="target_class",      # 被查班级作为行
                                columns="evaluator_class", # 评分者班级作为列
                                values="total",
                                aggfunc="mean"  # 周期内平均分（如果有多次评分）
                            ).round(2)
                            
                            if not pivot.empty:
                                sheet_name = f"第{period + 1}周期{matrix_grade}年级矩阵"[:31]
                                pivot.to_excel(writer, sheet_name=sheet_name)
                                print(f"✅ 创建{sheet_name}: {len(pivot.index)}个被评班级, {len(pivot.columns)}个评分班级")
                        except Exception as e:
                            print(f"⚠️ 跳过第{period + 1}周期{matrix_grade}年级矩阵创建: {str(e)}")
                
                # 3. 创建包含历史记录的详细明细表
                print("📝 正在生成详细明细表（包含历史记录）...")
                
                # 获取当前评分记录
                current_detail_df = month_df.copy()
                current_detail_df['记录类型'] = '当前评分'
                current_detail_df['评分周期'] = current_detail_df['period_number'].apply(lambda x: f"第{x + 1}周期")
                
                # 获取历史记录
                history_cur = conn.cursor()
                if is_sqlite:
                    history_sql = f"""
                        SELECT 
                            h.original_score_id, h.user_id, h.evaluator_name, h.evaluator_class,
                            h.target_grade, h.target_class, h.score1, h.score2, h.score3, h.total,
                            h.note, h.original_created_at as created_at, h.overwritten_at, h.overwritten_by_score_id
                        FROM scores_history h
                        WHERE strftime('%Y-%m', h.original_created_at) = {placeholder}{teacher_grade_filter}
                        ORDER BY h.original_created_at, h.overwritten_at
                    """
                else:
                    history_sql = f"""
                        SELECT 
                            h.original_score_id, h.user_id, h.evaluator_name, h.evaluator_class,
                            h.target_grade, h.target_class, h.score1, h.score2, h.score3, h.total,
                            h.note, h.original_created_at as created_at, h.overwritten_at, h.overwritten_by_score_id
                        FROM scores_history h
                        WHERE to_char(h.original_created_at, 'YYYY-MM') = {placeholder}{teacher_grade_filter}
                        ORDER BY h.original_created_at, h.overwritten_at
                    """
                
                history_cur.execute(history_sql, (month,))
                history_rows = history_cur.fetchall()
                
                if history_rows:
                    print(f"📚 找到{len(history_rows)}条历史记录")
                    history_df = pd.DataFrame(history_rows, columns=[
                        'id', 'user_id', 'evaluator_name', 'evaluator_class', 'target_grade', 
                        'target_class', 'score1', 'score2', 'score3', 'total', 
                        'note', 'created_at', 'overwritten_at', 'overwritten_by_score_id'
                    ])
                    
                    # 处理历史记录的时间
                    history_df["created_at"] = history_df["created_at"].apply(parse_datetime_robust)
                    history_df = history_df.dropna(subset=['created_at'])
                    
                    # 计算历史记录的周期（和当前记录使用相同逻辑）
                    history_df['date_only'] = history_df['created_at'].dt.date
                    history_df['period_number'] = history_df['date_only'].apply(lambda x: get_biweekly_period(x)[0])
                    history_df['period_end_date'] = history_df['date_only'].apply(lambda x: get_biweekly_period(x)[1])
                    history_df['period_month'] = history_df['period_end_date'].apply(lambda x: x.strftime('%Y-%m'))
                    
                    # 按周期归属过滤历史记录（和当前记录使用相同逻辑）
                    history_month_df = history_df[history_df['period_month'] == month].copy()
                    
                    if history_month_df.empty and not month_df.empty:
                        # 如果按周期归属没有历史记录，但有当前记录，回退到原始月份筛选
                        history_df['created_month'] = history_df['created_at'].dt.strftime('%Y-%m')
                        history_month_df = history_df[history_df['created_month'] == month].copy()
                        if not history_month_df.empty:
                            # 重新计算周期信息
                            history_month_df['date_only'] = history_month_df['created_at'].dt.date
                            history_month_df['period_number'] = history_month_df['date_only'].apply(lambda x: get_biweekly_period(x)[0])
                            history_month_df['period_end_date'] = history_month_df['date_only'].apply(lambda x: get_biweekly_period(x)[1])
                            history_month_df['period_month'] = history_month_df['period_end_date'].apply(lambda x: x.strftime('%Y-%m'))
                            print(f"⚠️ 历史记录按原始月份筛选: {len(history_month_df)}条")
                    
                    if not history_month_df.empty:
                        history_month_df['记录类型'] = '历史记录(已覆盖)'
                        history_month_df['评分周期'] = history_month_df['period_number'].apply(lambda x: f"第{x + 1}周期")
                        
                        print(f"✅ 最终历史记录: {len(history_month_df)}条")
                        
                        # 合并当前和历史记录
                        all_records = pd.concat([current_detail_df, history_month_df], ignore_index=True)
                    else:
                        print("📝 无匹配的历史记录")
                        all_records = current_detail_df
                else:
                    print("📝 无历史记录")
                    all_records = current_detail_df
                
                # 选择需要显示的列并排序
                detail_columns = ['记录类型', '评分周期', 'period_end_date', 'evaluator_class', 'target_grade', 'target_class', 'total', 'score1', 'score2', 'score3', 'note', 'created_at']
                detail_df = all_records[detail_columns].copy()
                detail_df.columns = ['记录类型', '评分周期', '周期结束日', '评分班级', '被查年级', '被查班级', '总分', '整洁分', '摆放分', '使用分', '备注', '评分时间']
                
                # 按评分时间顺序排序（解决排序混乱问题）
                detail_df = detail_df.sort_values(['评分时间', '记录类型'], ascending=[True, False])  # 先按时间，再按类型（当前记录在前）
                detail_df.to_excel(writer, sheet_name="提交明细", index=False)
                print(f"✅ 创建提交明细表: {len(detail_df)}条记录（包含历史记录）")
                
                print(f"📊 Excel导出完成，包含{len(month_df)}条评分记录")
        except Exception as e:
            raise Exception(f"Excel导出失败: {str(e)}")
        finally:
            # 确保数据库连接被关闭
            try:
                put_conn(conn)
            except Exception as e:
                print(f"Error: {e}")
                pass
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        try:
            put_conn(conn)
        except Exception as conn_error:
            print(f"数据库连接关闭错误: {conn_error}")
            pass
        return f"导出失败：{str(e)}", 500

@app.route('/admin')
@login_required
def admin():
    """管理员面板 - 管理员看全部数据，教师看本年级数据"""
    if not (current_user.is_admin() or current_user.is_teacher()):
        return "权限不足", 403
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # 获取统计数据
        import os
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        
        # 今日统计
        if is_sqlite:
            today_condition = "DATE(created_at) = DATE('now')"
            month_condition = "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
            date_format = "strftime('%Y-%m-%d', created_at)"
        else:
            today_condition = "DATE(created_at) = CURRENT_DATE"
            month_condition = "DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)"
            date_format = "to_char(created_at, 'YYYY-MM-DD')"
        
        # 教师只能查看本年级数据，但全校数据教师可以查看所有数据
        if current_user.is_teacher():
            # 检查是否是全校数据教师
            if current_user.class_name and ('全校' in current_user.class_name or 'ALL' in current_user.class_name.upper()):
                # 全校数据教师可以查看所有数据
                grade_filter = ""
                teacher_grade = None
            else:
                # 普通教师只能查看本年级数据
                # 从教师班级名称提取年级（如t6表示六年级，t7表示七年级等）
                teacher_grade = None
                if current_user.class_name:
                    class_name = current_user.class_name.lower()
                    if 't6' in class_name or '中预' in class_name:
                        teacher_grade = '中预'
                    elif 't7' in class_name or '初一' in class_name:
                        teacher_grade = '初一'
                    elif 't8' in class_name or '初二' in class_name:
                        teacher_grade = '初二'
                    elif 't10' in class_name or '高一' in class_name:
                        teacher_grade = '高一'
                    elif 't11' in class_name or '高二' in class_name:
                        teacher_grade = '高二'
                
                if not teacher_grade:
                    return f"无法确定教师所属年级，当前班级：{current_user.class_name}", 400
                
                # 添加年级过滤条件
                grade_filter = f"AND target_grade LIKE '%{teacher_grade}%'"
        else:
            # 管理员可以看全部
            grade_filter = ""
            teacher_grade = None
        
        # 统计总数
        cur.execute("SELECT COUNT(*) as total FROM users")
        total_users = cur.fetchone()['total']
        
        if current_user.is_teacher():
            # 检查是否是全校数据教师
            if current_user.class_name and ('全校' in current_user.class_name or 'ALL' in current_user.class_name.upper()):
                # 全校数据教师可以查看所有数据
                cur.execute("SELECT COUNT(*) as total FROM scores")
            else:
                # 普通教师只能查看本年级数据 - 使用参数化查询防止SQL注入
                cur.execute("SELECT COUNT(*) as total FROM scores WHERE target_grade LIKE ?", (f'%{teacher_grade}%',))
        else:
            cur.execute("SELECT COUNT(*) as total FROM scores")
        total_scores = cur.fetchone()['total']
        
        if current_user.is_teacher():
            if current_user.class_name and ('全校' in current_user.class_name or 'ALL' in current_user.class_name.upper()):
                cur.execute("SELECT AVG(total) as avg FROM scores")
            else:
                cur.execute("SELECT AVG(total) as avg FROM scores WHERE target_grade LIKE ?", (f'%{teacher_grade}%',))
        else:
            cur.execute("SELECT AVG(total) as avg FROM scores")
        avg_score = cur.fetchone()['avg'] or 0
        
        # 今日评分
        if current_user.is_teacher():
            if current_user.class_name and ('全校' in current_user.class_name or 'ALL' in current_user.class_name.upper()):
                cur.execute(f"SELECT COUNT(*) as today FROM scores WHERE {today_condition}")
            else:
                cur.execute(f"SELECT COUNT(*) as today FROM scores WHERE {today_condition} AND target_grade LIKE '%{teacher_grade}%'")
        else:
            cur.execute(f"SELECT COUNT(*) as today FROM scores WHERE {today_condition}")
        today_scores = cur.fetchone()['today']
        
        # 最近评分记录（根据教师类型显示不同数据）
        if current_user.is_teacher():
            if current_user.class_name and ('全校' in current_user.class_name or 'ALL' in current_user.class_name.upper()):
                # 全校数据教师看所有记录
                cur.execute('''
                    SELECT s.*, u.username, u.class_name as evaluator_class_name
                    FROM scores s 
                    JOIN users u ON s.user_id = u.id 
                    ORDER BY s.created_at DESC 
                    LIMIT 100
                ''')
            else:
                # 普通教师只看本年级
                cur.execute(f'''
                    SELECT s.*, u.username, u.class_name as evaluator_class_name
                    FROM scores s 
                    JOIN users u ON s.user_id = u.id 
                    WHERE s.target_grade LIKE '%{teacher_grade}%'
                    ORDER BY s.created_at DESC 
                    LIMIT 100
                ''')
        else:
            cur.execute('''
                SELECT s.*, u.username, u.class_name as evaluator_class_name
                FROM scores s 
                JOIN users u ON s.user_id = u.id 
                ORDER BY s.created_at DESC 
                LIMIT 100
            ''')
        recent_scores = cur.fetchall()
        
        # 环境信息
        import os
        import platform
        import sys
        import psutil
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        if db_url.startswith("postgresql"):
            db_type = "PostgreSQL"
        elif db_url.startswith("sqlite"):
            db_type = "SQLite"
        else:
            db_type = "其他"
        
        # 智能检测运行环境
        def detect_environment():
            """智能检测运行环境"""
            # 1. 检查是否有明确的FLASK_ENV设置
            flask_env = os.getenv("FLASK_ENV")
            if flask_env:
                return flask_env
            
            # 2. 检查常见的生产环境标识 - 最高优先级
            if os.getenv('RENDER') or os.getenv('HEROKU') or os.getenv('RAILWAY'):
                return "production"
            
            # 3. 检查数据库URL - PostgreSQL通常意味着生产环境
            db_url = os.getenv("DATABASE_URL", "")
            if db_url.startswith("postgresql://"):
                return "production"
            
            # 4. 检查是否有WSGI服务器标识
            server_software = os.getenv('SERVER_SOFTWARE', '')
            if 'waitress' in server_software.lower() or 'gunicorn' in server_software.lower():
                return "production"
            
            # 5. 检查Flask的debug模式 - 只在没有明确生产标识时才考虑
            if app.debug:
                return "development"
            
            # 6. 检查是否在开发服务器中运行 - 只在本地环境时才考虑
            if not os.getenv('RENDER') and not os.getenv('HEROKU') and not os.getenv('RAILWAY'):
                import __main__
                main_file = getattr(__main__, '__file__', '')
                if main_file and ('app.py' in main_file or 'run.py' in main_file):
                    return "development"
            
            # 7. 默认判断：有PostgreSQL连接 = 生产环境
            return "production" if db_url.startswith("postgresql://") else "development"

        detected_env = detect_environment()
        
        # 检测实际运行的服务器类型
        def detect_actual_server():
            """检测实际正在运行的服务器类型"""
            import sys
            import threading
            
            # 1. 检查环境变量中的服务器信息
            server_software = os.getenv('SERVER_SOFTWARE', '')
            if 'waitress' in server_software.lower():
                return "Waitress (WSGI)"
            elif 'gunicorn' in server_software.lower():
                return "Gunicorn (WSGI)" 
            elif 'uwsgi' in server_software.lower():
                return "uWSGI (WSGI)"
            
            # 2. 检查进程模块导入情况
            try:
                # 检查是否导入了waitress相关模块
                if any('waitress' in name for name in sys.modules.keys()):
                    return "Waitress (WSGI)"
                if any('gunicorn' in name for name in sys.modules.keys()):
                    return "Gunicorn (WSGI)"
                if any('uwsgi' in name for name in sys.modules.keys()):
                    return "uWSGI (WSGI)"
            except Exception:
                pass
            
            # 3. 检查线程名称（Waitress会创建特定的线程）
            try:
                thread_names = [t.name for t in threading.enumerate()]
                if any('waitress' in name.lower() for name in thread_names):
                    return "Waitress (WSGI)"
                if any('gunicorn' in name.lower() for name in thread_names):
                    return "Gunicorn (WSGI)"
            except Exception:
                pass
            
            # 4. 检查是否在生产环境的WSGI服务器中运行
            if os.getenv('RENDER') or os.getenv('HEROKU') or os.getenv('RAILWAY'):
                # 生产环境，推断使用的WSGI服务器
                return "Waitress (WSGI)" if platform.system() == "Windows" else "Gunicorn (WSGI)"
            
            # 5. 检查是否通过app.run()直接运行
            import __main__
            main_file = getattr(__main__, '__file__', '')
            if main_file and ('app.py' in main_file or 'run.py' in main_file):
                # 进一步检查是否真的是Flask开发服务器
                if app.debug:
                    return "Flask 开发服务器 (Debug)"
                else:
                    return "Flask 开发服务器"
            
            # 6. 根据debug模式和其他特征判断
            if app.debug:
                return "Flask 开发服务器 (Debug)"
            
            # 7. 检查命令行参数
            try:
                import sys
                cmd_line = ' '.join(sys.argv)
                if 'waitress-serve' in cmd_line or 'waitress' in cmd_line:
                    return "Waitress (WSGI)"
                if 'gunicorn' in cmd_line:
                    return "Gunicorn (WSGI)"
            except Exception:
                pass
            
            # 默认情况
            return "未知服务器"
        
        actual_server = detect_actual_server()
        
        # 运行环境信息 - 只有admin能看到
        environment_info = None
        if current_user.is_admin():
            environment_info = {
                'database_type': db_type,
                'database_url': db_url.split('@')[-1] if '@' in db_url else db_url,  # 隐藏敏感信息
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'platform': platform.platform(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': f"{psutil.virtual_memory().total // (1024**3)} GB",
                'memory_available': f"{psutil.virtual_memory().available // (1024**3)} GB",
                'flask_env': detected_env,
                'flask_env_var': os.getenv("FLASK_ENV", "未设置"),
                'debug_mode': app.debug,
                'wsgi_server': actual_server,
                'server_software': os.getenv('SERVER_SOFTWARE', '直接运行')
            }

        # 年级统计（VCE年级合并，根据教师类型显示不同数据）
        grade_stats = []
        try:
            if current_user.is_teacher():
                # 检查是否是全校数据教师
                if current_user.class_name and ('全校' in current_user.class_name or 'ALL' in current_user.class_name.upper()):
                    # 全校数据教师看年级分布
                    cur.execute('''
                        SELECT 
                            CASE 
                                WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                                ELSE target_grade 
                            END as display_grade,
                            COUNT(*) as count, 
                            AVG(total) as avg_score
                        FROM scores 
                        GROUP BY 
                            CASE 
                                WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                                ELSE target_grade 
                            END
                        ORDER BY 
                            CASE 
                                WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                                ELSE target_grade 
                            END
                    ''')
                    grade_stats = cur.fetchall()
                else:
                    # 普通教师看本年级各班级的本周期完成情况
                    # 使用学期配置计算当前周期
                    try:
                        config_data = get_current_semester_config(conn)
                        if config_data:
                            period_info = calculate_period_info(semester_config=config_data['semester'])
                        else:
                            # 回退到默认逻辑
                            period_info = calculate_period_info()
                        
                        period_start = period_info['period_start']
                        period_end = period_info['period_end']
                        period_number = period_info['period_number']
                        
                        # 高一高二教师需要包含对应的VCE班级
                        if teacher_grade in ['高一', '高二']:
                            teacher_grades = [teacher_grade, f'{teacher_grade}VCE']
                        else:
                            teacher_grades = [teacher_grade]
                        
                        # 尝试基于学期配置中的活跃班级查询
                        grade_placeholders = ','.join(['?' for _ in teacher_grades])
                        cur.execute(f'''
                            SELECT 
                                sc.class_name as display_grade,
                                CASE WHEN COUNT(s.id) > 0 THEN 1 ELSE 0 END as count, 
                                CASE WHEN COUNT(s.id) > 0 THEN 8.5 ELSE 0 END as avg_score
                            FROM semester_classes sc
                            LEFT JOIN users u ON sc.class_name = u.class_name AND u.role = 'student'
                            LEFT JOIN scores s ON u.id = s.user_id 
                                AND DATE(s.created_at) >= ? 
                                AND DATE(s.created_at) <= ?
                            WHERE sc.is_active = 1 
                                AND sc.semester_id = (SELECT id FROM semester_config WHERE is_active = 1)
                                AND sc.grade_name IN ({grade_placeholders})
                            GROUP BY sc.class_name, sc.grade_name
                            ORDER BY 
                                CASE sc.grade_name 
                                    WHEN '中预' THEN 1 
                                    WHEN '初一' THEN 2 
                                    WHEN '初二' THEN 3 
                                    WHEN '高一' THEN 4 
                                    WHEN '高二' THEN 5 
                                    WHEN '高一VCE' THEN 6 
                                    WHEN '高二VCE' THEN 7 
                                    ELSE 8 
                                END, 
                                sc.class_name
                        ''', [period_start.strftime('%Y-%m-%d'), period_end.strftime('%Y-%m-%d')] + teacher_grades)
                        grade_stats = cur.fetchall()
                    except Exception as semester_error:
                        print(f"学期配置查询失败，回退到简单统计: {semester_error}")
                        # 回退到简单的年级统计
                        cur.execute('''
                            SELECT 
                                CASE 
                                    WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                                    ELSE target_grade 
                                END as display_grade,
                                COUNT(*) as count, 
                                AVG(total) as avg_score
                            FROM scores 
                            WHERE target_grade LIKE ?
                            GROUP BY 
                                CASE 
                                    WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                                    ELSE target_grade 
                                END
                            ORDER BY 
                                CASE 
                                    WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                                    ELSE target_grade 
                                END
                        ''', (f'%{teacher_grade}%',))
                        grade_stats = cur.fetchall()
            else:
                # 管理员看年级分布
                cur.execute('''
                    SELECT 
                        CASE 
                            WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                            ELSE target_grade 
                        END as display_grade,
                        COUNT(*) as count, 
                        AVG(total) as avg_score
                    FROM scores 
                    GROUP BY 
                        CASE 
                            WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                            ELSE target_grade 
                        END
                    ORDER BY 
                        CASE 
                            WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                            ELSE target_grade 
                        END
                ''')
                grade_stats = cur.fetchall()
        except Exception as grade_error:
            print(f"年级统计查询失败: {grade_error}")
            grade_stats = []  # 设置为空列表，避免页面崩溃
        
        # 每日趋势（最近7天，根据教师类型显示不同数据）
        daily_trend = []
        try:
            if current_user.is_teacher():
                if current_user.class_name and ('全校' in current_user.class_name or 'ALL' in current_user.class_name.upper()):
                    # 全校数据教师看所有趋势
                    if is_sqlite:
                        cur.execute(f'''
                            SELECT {date_format} as date, COUNT(*) as count
                            FROM scores 
                            WHERE created_at >= datetime('now', '-7 days')
                            GROUP BY {date_format}
                            ORDER BY date
                        ''')
                    else:
                        cur.execute(f'''
                            SELECT {date_format} as date, COUNT(*) as count
                            FROM scores 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                            GROUP BY {date_format}
                            ORDER BY date
                        ''')
                else:
                    # 普通教师只看本年级趋势
                    if is_sqlite:
                        cur.execute(f'''
                            SELECT {date_format} as date, COUNT(*) as count
                            FROM scores 
                            WHERE created_at >= datetime('now', '-7 days') AND target_grade LIKE '%{teacher_grade}%'
                            GROUP BY {date_format}
                            ORDER BY date
                        ''')
                    else:
                        cur.execute(f'''
                            SELECT {date_format} as date, COUNT(*) as count
                            FROM scores 
                            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' AND target_grade LIKE '%{teacher_grade}%'
                            GROUP BY {date_format}
                            ORDER BY date
                        ''')
            else:
                if is_sqlite:
                    cur.execute(f'''
                        SELECT {date_format} as date, COUNT(*) as count
                        FROM scores 
                        WHERE created_at >= datetime('now', '-7 days')
                        GROUP BY {date_format}
                        ORDER BY date
                    ''')
                else:
                    cur.execute(f'''
                        SELECT {date_format} as date, COUNT(*) as count
                        FROM scores 
                        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                        GROUP BY {date_format}
                        ORDER BY date
                    ''')
            daily_trend = cur.fetchall()
        except Exception as trend_error:
            print(f"每日趋势查询失败: {trend_error}")
            daily_trend = []  # 设置为空列表，避免页面崩溃
        
        # 当前月份
        from datetime import datetime
        current_month = datetime.now().strftime('%Y-%m')
        today = datetime.now().strftime('%Y-%m-%d')
        
        return render_template('admin.html', 
                             user=current_user,
                             total_users=total_users,
                             total_scores=total_scores,
                             avg_score=avg_score,
                             today_scores=today_scores,
                             recent_scores=recent_scores,
                             grade_stats=grade_stats,
                             daily_trend=daily_trend,
                             current_month=current_month,
                             today=today,
                             environment_info=environment_info)
    except Exception as e:
        import traceback
        print(f"Admin 页面错误: {e}")
        print(f"详细堆栈: {traceback.format_exc()}")
        # 返回错误信息，帮助调试
        return f"Admin 页面错误: {str(e)}<br><br>详细信息:<br><pre>{traceback.format_exc()}</pre>", 500
    finally:
        put_conn(conn)

@app.route('/success')
@login_required
def success():
    """评分提交成功页面"""
    return render_template('success.html', user=current_user)

@app.route('/api/stats')
@login_required
def api_stats():
    """获取统计数据"""
    conn = get_conn()
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        cur = conn.cursor()
        
        # 今日统计
        if is_sqlite:
            today_condition = "DATE(created_at) = DATE('now')"
            month_condition = "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        else:
            today_condition = "DATE(created_at) = CURRENT_DATE"
            month_condition = "DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)"
        
        # 今日统计
        cur.execute(f"""
            SELECT 
                COUNT(*) as total_scores,
                AVG(total) as avg_score,
                COUNT(DISTINCT evaluator_class) as active_classes
            FROM scores 
            WHERE {today_condition}
        """)
        today_stats = cur.fetchone()
        
        # 本月统计
        cur.execute(f"""
            SELECT 
                COUNT(*) as total_scores,
                AVG(total) as avg_score,
                COUNT(DISTINCT evaluator_class) as active_classes
            FROM scores 
            WHERE {month_condition}
        """)
        month_stats = cur.fetchone()
        
        # 各年级平均分（VCE年级合并）
        cur.execute(f"""
            SELECT 
                CASE 
                    WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                    ELSE target_grade 
                END as display_grade,
                AVG(total) as avg_score,
                COUNT(*) as count
            FROM scores 
            WHERE {today_condition}
            GROUP BY 
                CASE 
                    WHEN target_grade LIKE '%VCE%' THEN 'VCE'
                    ELSE target_grade 
                END
            ORDER BY avg_score DESC
        """)
        grade_stats = cur.fetchall()
        
        return jsonify({
            'today': dict(today_stats),
            'month': dict(month_stats),
            'grade_stats': [dict(row) for row in grade_stats]
        })
    finally:
        put_conn(conn)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == "__main__":
    # 简化的启动逻辑：更可靠的数据库初始化
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # 检查关键表是否存在
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_exists = cur.fetchone()
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='semester_config'")
        semester_exists = cur.fetchone()
        
        put_conn(conn)
        
        # 如果关键表不存在，执行完整初始化
        if not users_exists or not semester_exists:
            print("检测到数据库不完整，执行初始化...")
            print(f"users表存在: {users_exists is not None}")
            print(f"semester_config表存在: {semester_exists is not None}")
            
            from init_db import init_database
            init_database()
            print("✅ 数据库初始化完成")
        else:
            print("✅ 数据库表完整，连接正常")
            
    except Exception as e:
        print(f"数据库检查失败: {e}")
        print("尝试完整初始化...")
        try:
            from init_db import init_database
            init_database()
            print("✅ 数据库初始化完成")
        except Exception as init_e:
            print(f"❌ 数据库初始化失败: {init_e}")
            print("请检查数据库配置和权限")
    
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)