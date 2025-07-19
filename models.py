from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

class User(UserMixin):
    def __init__(self, id, username, role='student', class_name=None):
        self.id = id
        self.username = username
        self.role = role  # student, admin, teacher
        self.class_name = class_name
        self.password_hash = None
    
    @staticmethod
    def get_user_by_id(user_id, conn):
        """根据ID获取用户信息"""
        cur = conn.cursor()
        # 检测数据库类型
        import os
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        placeholder = "?" if db_url.startswith("sqlite") else "%s"
        
        cur.execute(f"""
            SELECT id, username, role, class_name 
            FROM users WHERE id = {placeholder}
        """, (user_id,))
        row = cur.fetchone()
        if row:
            return User(row['id'], row['username'], 
                       row['role'], row['class_name'])
        return None
    
    @staticmethod
    def get_user_by_username(username, conn):
        """根据用户名获取用户信息"""
        cur = conn.cursor()
        import os
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        placeholder = "?" if db_url.startswith("sqlite") else "%s"
        
        cur.execute(f"""
            SELECT id, username, password_hash, role, class_name 
            FROM users WHERE username = {placeholder}
        """, (username,))
        row = cur.fetchone()
        if row:
            user = User(row['id'], row['username'], 
                       row['role'], row['class_name'])
            user.password_hash = row['password_hash']
            return user
        return None
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """检查是否为管理员"""
        return self.role == 'admin'
    
    def is_teacher(self):
        """检查是否为老师"""
        return self.role == 'teacher'

class Score:
    def __init__(self, id, user_id, evaluator_name, evaluator_class, 
                 target_grade, target_class, score1, score2, score3, 
                 total, note, created_at):
        self.id = id
        self.user_id = user_id
        self.evaluator_name = evaluator_name
        self.evaluator_class = evaluator_class
        self.target_grade = target_grade
        self.target_class = target_class
        self.score1 = score1
        self.score2 = score2
        self.score3 = score3
        self.total = total
        self.note = note
        self.created_at = created_at
    
    @staticmethod
    def create_score(user_id, evaluator_name, evaluator_class, target_grade, 
                    target_class, score1, score2, score3, note, conn):
        """创建新的评分记录（支持软删除和覆盖）"""
        cur = conn.cursor()
        
        import os
        from datetime import datetime, timedelta
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        # 验证分数范围
        if not (0 <= score1 <= 3):
            return None, "电脑整洁分数必须在0-3之间", 0
        if not (0 <= score2 <= 3):
            return None, "物品摆放分数必须在0-3之间", 0
        if not (0 <= score3 <= 4):
            return None, "使用情况分数必须在0-4之间", 0
        
        # 计算两周评分周期
        def get_biweekly_period_end(date):
            """计算日期所属的两周周期结束日"""
            # 找到该日期所在的周日（本周或下周）
            days_until_sunday = (6 - date.weekday()) % 7
            if days_until_sunday == 0 and date.weekday() != 6:
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
            
            return period_end_sunday
        
        now = datetime.now()
        current_date = now.date()
        period_end = get_biweekly_period_end(current_date)
        
        # 检查是否已评分（同一评分周期内）
        if is_sqlite:
            # 查找同一评分周期内的现有评分
            cur.execute(f"""
                SELECT id, created_at FROM scores 
                WHERE user_id = {placeholder} AND target_grade = {placeholder} AND target_class = {placeholder}
                ORDER BY created_at DESC
            """, (user_id, target_grade, target_class))
        else:
            cur.execute(f"""
                SELECT id, created_at FROM scores 
                WHERE user_id = {placeholder} AND target_grade = {placeholder} AND target_class = {placeholder}
                ORDER BY created_at DESC
            """, (user_id, target_grade, target_class))
        
        existing_scores = cur.fetchall()
        overwrite_count = 0
        
        # 检查是否有同一周期的评分需要归档
        for existing_score in existing_scores:
            existing_created = existing_score['created_at']
            if isinstance(existing_created, str):
                existing_created = datetime.fromisoformat(existing_created.replace('Z', '+00:00'))
            if hasattr(existing_created, 'date'):
                existing_date = existing_created.date()
            else:
                existing_date = existing_created
            
            existing_period_end = get_biweekly_period_end(existing_date)
            
            # 如果在同一个评分周期内，需要归档旧记录
            if existing_period_end == period_end:
                existing_id = existing_score['id']
                
                # 获取完整的旧记录信息
                cur.execute(f"""
                    SELECT * FROM scores WHERE id = {placeholder}
                """, (existing_id,))
                old_record = cur.fetchone()
                
                if old_record:
                    # 归档到历史表
                    cur.execute(f"""
                        INSERT INTO scores_history 
                        (original_score_id, user_id, evaluator_name, evaluator_class, 
                         target_grade, target_class, score1, score2, score3, total, note, 
                         original_created_at, overwritten_at, overwritten_by_score_id)
                        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                                {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                                {placeholder}, {placeholder}, {placeholder})
                    """, (old_record['id'], old_record['user_id'], old_record['evaluator_name'], 
                          old_record['evaluator_class'], old_record['target_grade'], old_record['target_class'],
                          old_record['score1'], old_record['score2'], old_record['score3'], old_record['total'], 
                          old_record['note'], old_record['created_at'], now, 0))  # overwritten_by_score_id将在插入新记录后更新
                    
                    # 删除旧记录
                    cur.execute(f"""
                        DELETE FROM scores WHERE id = {placeholder}
                    """, (existing_id,))
                    
                    overwrite_count += 1
        
        total = score1 + score2 + score3
        created_at = now
        
        try:
            # 插入新记录
            if is_sqlite:
                cur.execute(f"""
                    INSERT INTO scores (user_id, evaluator_name, evaluator_class, 
                                      target_grade, target_class, score1, score2, score3, 
                                      total, note, created_at)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                            {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                """, (user_id, evaluator_name, evaluator_class, target_grade, 
                      target_class, score1, score2, score3, total, note, created_at))
                score_id = cur.lastrowid
            else:
                cur.execute(f"""
                    INSERT INTO scores (user_id, evaluator_name, evaluator_class, 
                                      target_grade, target_class, score1, score2, score3, 
                                      total, note, created_at)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
                            {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                    RETURNING id
                """, (user_id, evaluator_name, evaluator_class, target_grade, 
                      target_class, score1, score2, score3, total, note, created_at))
                score_id = cur.fetchone()['id']
            
            # 更新历史记录中的overwritten_by_score_id
            if overwrite_count > 0:
                cur.execute(f"""
                    UPDATE scores_history 
                    SET overwritten_by_score_id = {placeholder}
                    WHERE overwritten_by_score_id = 0 AND overwritten_at = {placeholder}
                """, (score_id, now))
            
            conn.commit()
            return score_id, None, overwrite_count
        except Exception as e:
            conn.rollback()
            return None, f"数据库错误: {str(e)}", 0
    
    @staticmethod
    def get_user_scores(user_id, conn, limit=50):
        """获取用户的评分历史"""
        cur = conn.cursor()
        import os
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        placeholder = "?" if db_url.startswith("sqlite") else "%s"
        
        cur.execute(f"""
            SELECT * FROM scores 
            WHERE user_id = {placeholder} 
            ORDER BY created_at DESC 
            LIMIT {placeholder}
        """, (user_id, limit))
        return cur.fetchall()
    
    @staticmethod
    def get_scores_by_date_range(start_date, end_date, conn):
        """按日期范围获取评分"""
        cur = conn.cursor()
        import os
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        placeholder = "?" if db_url.startswith("sqlite") else "%s"
        
        cur.execute(f"""
            SELECT * FROM scores 
            WHERE created_at BETWEEN {placeholder} AND {placeholder}
            ORDER BY created_at DESC
        """, (start_date, end_date))
        return cur.fetchall()