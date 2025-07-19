# 数据库初始化脚本
import os
import sys
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_conn, put_conn

load_dotenv()

def init_database():
    """初始化数据库表结构"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        
        if is_sqlite:
            # SQLite表结构
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'admin')),
                    class_name VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # 创建评分表（SQLite版本）
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    evaluator_name VARCHAR(50) NOT NULL,
                    evaluator_class VARCHAR(50) NOT NULL,
                    target_grade VARCHAR(20) NOT NULL,
                    target_class VARCHAR(50) NOT NULL,
                    score1 INTEGER CHECK (score1 BETWEEN 0 AND 3),
                    score2 INTEGER CHECK (score2 BETWEEN 0 AND 3),
                    score3 INTEGER CHECK (score3 BETWEEN 0 AND 4),
                    total INTEGER NOT NULL,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建评分历史表（用于软删除和覆盖追踪）
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scores_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_score_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    evaluator_name VARCHAR(50) NOT NULL,
                    evaluator_class VARCHAR(50) NOT NULL,
                    target_grade VARCHAR(20) NOT NULL,
                    target_class VARCHAR(50) NOT NULL,
                    score1 INTEGER CHECK (score1 BETWEEN 0 AND 3),
                    score2 INTEGER CHECK (score2 BETWEEN 0 AND 3),
                    score3 INTEGER CHECK (score3 BETWEEN 0 AND 4),
                    total INTEGER NOT NULL,
                    note TEXT,
                    original_created_at TIMESTAMP NOT NULL,
                    overwritten_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    overwritten_by_score_id INTEGER DEFAULT 0
                )
            """)
            
        else:
            # PostgreSQL表结构
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'admin')),
                    class_name VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    evaluator_name VARCHAR(50) NOT NULL,
                    evaluator_class VARCHAR(50) NOT NULL,
                    target_grade VARCHAR(20) NOT NULL,
                    target_class VARCHAR(50) NOT NULL,
                    score1 INTEGER CHECK (score1 BETWEEN 0 AND 3),
                    score2 INTEGER CHECK (score2 BETWEEN 0 AND 3),
                    score3 INTEGER CHECK (score3 BETWEEN 0 AND 4),
                    total INTEGER GENERATED ALWAYS AS (score1 + score2 + score3) STORED,
                    note TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建评分历史表（PostgreSQL版本）
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scores_history (
                    id SERIAL PRIMARY KEY,
                    original_score_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    evaluator_name VARCHAR(50) NOT NULL,
                    evaluator_class VARCHAR(50) NOT NULL,
                    target_grade VARCHAR(20) NOT NULL,
                    target_class VARCHAR(50) NOT NULL,
                    score1 INTEGER CHECK (score1 BETWEEN 0 AND 3),
                    score2 INTEGER CHECK (score2 BETWEEN 0 AND 3),
                    score3 INTEGER CHECK (score3 BETWEEN 0 AND 4),
                    total INTEGER NOT NULL,
                    note TEXT,
                    original_created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    overwritten_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    overwritten_by_score_id INTEGER DEFAULT 0
                )
            """)
        
        # 创建索引优化查询
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scores_user_id ON scores(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_scores_target_class ON scores(target_class)",
            "CREATE INDEX IF NOT EXISTS idx_scores_created_at ON scores(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_scores_grade_date ON scores(target_grade, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_scores_history_original ON scores_history(original_score_id)",
            "CREATE INDEX IF NOT EXISTS idx_scores_history_overwritten ON scores_history(overwritten_by_score_id)",
            "CREATE INDEX IF NOT EXISTS idx_scores_history_user ON scores_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_scores_history_date ON scores_history(original_created_at)"
        ]
        for index_sql in indexes:
            cur.execute(index_sql)
        
        # 创建管理员账户（如果环境变量中提供了）
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@school.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if admin_username and admin_email and admin_password:
            # 检查管理员是否已存在
            placeholder = "?" if is_sqlite else "%s"
            cur.execute(f"SELECT id FROM users WHERE username = {placeholder}", (admin_username,))
            if not cur.fetchone():
                password_hash = generate_password_hash(admin_password)
                cur.execute(f"""
                    INSERT INTO users (username, password_hash, role, class_name)
                    VALUES ({placeholder}, {placeholder}, 'admin', '管理员')
                """, (admin_username, password_hash))
                print(f"管理员账户创建成功: {admin_username}")
        
        # 创建一些测试学生账户
        test_students = [
            ('student1', 'student123', '中预1班'),
            ('student2', 'student123', '初一2班'),
            ('student3', 'student123', '初二3班'),
        ]
        
        placeholder = "?" if is_sqlite else "%s"
        for username, password, class_name in test_students:
            cur.execute(f"SELECT id FROM users WHERE username = {placeholder}", (username,))
            if not cur.fetchone():
                password_hash = generate_password_hash(password)
                cur.execute(f"""
                    INSERT INTO users (username, password_hash, role, class_name)
                    VALUES ({placeholder}, {placeholder}, 'student', {placeholder})
                """, (username, password_hash, class_name))
                print(f"测试学生账户创建成功: {username}")
        
        conn.commit()
        print("数据库初始化完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"数据库初始化失败: {e}")
        raise
    finally:
        put_conn(conn)

if __name__ == "__main__":
    init_database()