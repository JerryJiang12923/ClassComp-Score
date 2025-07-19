#!/usr/bin/env python3
"""创建新的用户数据库，使用g6c1/g11c8命名规则
每个班只有一个信息委员"""
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_users_db():
    """创建新的用户数据库"""
    conn = sqlite3.connect('classcomp.db')
    conn.row_factory = sqlite3.Row
    
# 创建用户表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('student', 'teacher', 'admin')),
            class_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建评分表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            evaluator_name TEXT NOT NULL,
            evaluator_class TEXT NOT NULL,
            target_grade TEXT NOT NULL,
            target_class TEXT NOT NULL,
            score1 INTEGER CHECK (score1 BETWEEN 0 AND 3),
            score2 INTEGER CHECK (score2 BETWEEN 0 AND 3),
            score3 INTEGER CHECK (score3 BETWEEN 0 AND 4),
            total INTEGER NOT NULL,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 年级和班级映射
    grade_mapping = {
        '6': '中预',
        '7': '初一', 
        '8': '初二',
        '9': '初三',
        '10': '高一',
        '11': '高二',
        '12': '高三'
    }
    
    # 班级配置
    class_config = {
        '6': 8,   # 中预1-8班
        '7': 8,   # 初一1-8班
        '8': 8,   # 初二1-8班
        '9': 8,   # 初三1-8班
        '10': 8,  # 高一1-8班
        '11': 8,  # 高二1-8班
        '12': 8   # 高三1-8班
    }
    
    users = []
    default_password = 'student123'
    password_hash = generate_password_hash(default_password)
    
    # 创建管理员
    users.append(('admin', password_hash, 'admin', '管理员'))
    
    # 创建信息委员（每个班一个）
    for grade_num, grade_name in grade_mapping.items():
        class_count = class_config[grade_num]
        for class_num in range(1, class_count + 1):
            username = f'g{grade_num}c{class_num}'
            class_name = f'{grade_name}{class_num}班'
            users.append((username, password_hash, 'student', class_name))
    
    # 创建教师账户（每个年级一个信息老师）
    teacher_password = 'teacher123'
    teacher_hash = generate_password_hash(teacher_password)
    
    for grade_num, grade_name in grade_mapping.items():
        username = f't{grade_num}'
        class_name = f'{grade_name}老师'
        users.append((username, teacher_hash, 'teacher', class_name))
    
    # 插入所有用户
    conn.executemany(
        'INSERT OR IGNORE INTO users (username, password_hash, role, class_name) VALUES (?, ?, ?, ?)',
        users
    )
    
    conn.commit()
    
    # 统计信息
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    students = conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    teachers = conn.execute("SELECT COUNT(*) FROM users WHERE role='teacher'").fetchone()[0]
    admins = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
    
    print("=== 用户数据库创建完成 ===")
    print(f"总用户数: {total_users}")
    print(f"信息委员: {students}人")
    print(f"教师: {teachers}人") 
    print(f"管理员: {admins}人")
    
    # 显示部分用户
    print("\n=== 信息委员列表 ===")
    cur = conn.execute('SELECT username, class_name FROM users WHERE role="student" ORDER BY class_name')
    for row in cur.fetchall():
        print(f"{row['username']} - {row['class_name']}")
    
    conn.close()

if __name__ == "__main__":
    create_users_db()