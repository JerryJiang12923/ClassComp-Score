import os
from datetime import datetime, timedelta
import pytz
from flask import Flask, request, jsonify, render_template, url_for, send_file, redirect, session, flash
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import pandas as pd
from werkzeug.security import generate_password_hash

from db import get_conn, put_conn
from models import User, Score
from forms import LoginForm, RegistrationForm, ScoreForm

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

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
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
    
    return render_template('index.html', user=current_user, auto_target_grade=target_grade)

@app.route('/login', methods=['GET', 'POST'])
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
    """管理员用户管理 - 校内用户管理"""
    if not current_user.is_admin():
        return "权限不足", 403
    
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
        
        # 查看所有用户及评分统计
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
                u.class_name,
                u.username
        ''')
        users = cur.fetchall()
        return render_template('admin_users.html', users=users, user=current_user)
        
    finally:
        put_conn(conn)

@app.route('/submit_scores', methods=['POST'])
@login_required
def submit_scores():
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, message="无效的请求数据"), 400
        
        # 验证必填字段
        required_fields = ["target_grade", "scores"]
        if not all(field in data for field in required_fields):
            return jsonify(success=False, message="缺少必要字段"), 400
        
        conn = get_conn()
        
        try:
            # 批量插入评分
            inserted_count = 0
            total_overwrite_count = 0
            errors = []
            for score_data in data["scores"]:
                try:
                    score1 = int(score_data["score1"])
                    score2 = int(score_data["score2"])
                    score3 = int(score_data["score3"])
                    
                    score_id, error, overwrite_count = Score.create_score(
                        user_id=current_user.id,
                        evaluator_name=current_user.username,
                        evaluator_class=current_user.class_name,
                        target_grade=data["target_grade"],
                        target_class=score_data["className"],
                        score1=score1,
                        score2=score2,
                        score3=score3,
                        note=score_data.get("note", ""),
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
    """查看评分历史 - 管理员看全部，用户看个人"""
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
        else:
            # 普通用户只看个人评分
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
    """导出Excel月度报告"""
    if not (current_user.is_admin() or current_user.is_teacher()):
        return "权限不足", 403
    
    month = request.args.get("month")
    if not month:
        return "请提供 month=YYYY-MM 查询参数", 400
    
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        import os
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
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
                WHERE strftime('%Y-%m', created_at) = {placeholder}
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
                WHERE to_char(created_at, 'YYYY-MM') = {placeholder}
                ORDER BY created_at
            """
        cur.execute(sql, (month,))
        rows = cur.fetchall()
        # 不要在这里关闭连接，后面还需要查询历史记录
        # put_conn(conn)
        
        if not rows:
            put_conn(conn)  # 提前返回时关闭连接
            return "当月无数据", 200
            
        df = pd.DataFrame(rows, columns=[
            'id', 'evaluator_name', 'evaluator_class', 'target_grade', 
            'target_class', 'score1', 'score2', 'score3', 'total', 
            'note', 'created_at'
        ])
        
        print(f"📊 导出前数据总数: {len(df)}")
        
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
            except:
                try:
                    # 如果失败，尝试只取日期部分
                    date_part = dt_str.split()[0]
                    return pd.to_datetime(date_part)
                except:
                    print(f"⚠️ 无法解析时间: {dt_str}")
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
        
        filename = f"评分表_{month.replace('-', '')}.xlsx"
        filepath = os.path.join(EXPORT_FOLDER, filename)
        
        try:
            with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
                print(f"开始创建Excel报表... 共{len(df)}条记录")
                
                # 计算每条记录的评分周期
                df['date_only'] = df['created_at'].dt.date
                
                # 计算每个日期所属的两周周期
                def get_biweekly_period(date):
                    # 找到该日期所在的周日（本周或下周）
                    days_until_sunday = (6 - date.weekday()) % 7
                    if days_until_sunday == 0 and date.weekday() != 6:  # 如果是周一到周六
                        days_until_sunday = 7
                    current_sunday = date + timedelta(days=days_until_sunday)
                    
                    # 计算从年初开始的周数
                    year_start = datetime(date.year, 1, 1).date()
                    days_from_start = (current_sunday - year_start).days
                    week_number = days_from_start // 7
                    
                    # 两周为一个周期
                    period_number = week_number // 2
                    period_end_sunday = year_start + timedelta(days=(period_number * 14 + 13))
                    
                    # 确保周期结束日是周日
                    while period_end_sunday.weekday() != 6:
                        period_end_sunday += timedelta(days=1)
                    
                    return period_number, period_end_sunday
                
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
                    
                    for matrix_grade in period_df_copy["matrix_grade"].unique():
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
                        WHERE strftime('%Y-%m', h.original_created_at) = {placeholder}
                        ORDER BY h.original_created_at, h.overwritten_at
                    """
                else:
                    history_sql = f"""
                        SELECT 
                            h.original_score_id, h.user_id, h.evaluator_name, h.evaluator_class,
                            h.target_grade, h.target_class, h.score1, h.score2, h.score3, h.total,
                            h.note, h.original_created_at as created_at, h.overwritten_at, h.overwritten_by_score_id
                        FROM scores_history h
                        WHERE to_char(h.original_created_at, 'YYYY-MM') = {placeholder}
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
            except:
                pass
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        try:
            put_conn(conn)
        except:
            pass
        return f"导出失败：{str(e)}", 500

@app.route('/admin')
@login_required
def admin():
    """管理员面板 - 提供完整数据"""
    if not current_user.is_admin():
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
        
        # 统计总数
        cur.execute("SELECT COUNT(*) as total FROM users")
        total_users = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM scores")
        total_scores = cur.fetchone()['total']
        
        cur.execute("SELECT AVG(total) as avg FROM scores")
        avg_score = cur.fetchone()['avg'] or 0
        
        # 今日评分
        cur.execute(f"SELECT COUNT(*) as today FROM scores WHERE {today_condition}")
        today_scores = cur.fetchone()['today']
        
        # 最近评分记录
        cur.execute('''
            SELECT s.*, u.username, u.class_name as evaluator_class_name
            FROM scores s 
            JOIN users u ON s.user_id = u.id 
            ORDER BY s.created_at DESC 
            LIMIT 100
        ''')
        recent_scores = cur.fetchall()
        
        # 年级统计（VCE年级合并）
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
        
        # 每日趋势（最近7天）
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
                             today=today)
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
        import os
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
    # 只在数据库不存在或连接失败时才初始化
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        put_conn(conn)
        print("数据库连接正常")
    except Exception as e:
        print(f"数据库连接失败，开始初始化: {e}")
        try:
            from init_db import init_database
            init_database()
            print("数据库初始化完成")
        except Exception as init_e:
            print(f"数据库初始化失败: {init_e}")
    
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)