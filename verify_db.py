#!/usr/bin/env python3
import sqlite3

# 连接数据库
conn = sqlite3.connect('classcomp.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 查看所有表
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("📊 数据库表:")
for table in tables:
    print(f"  - {table['name']}")

print("\n📋 scores 表结构:")
cur.execute("PRAGMA table_info(scores)")
for col in cur.fetchall():
    print(f"  {col['name']}: {col['type']}")

print("\n📋 scores_history 表结构:")
cur.execute("PRAGMA table_info(scores_history)")
for col in cur.fetchall():
    print(f"  {col['name']}: {col['type']}")

print("\n👥 用户数据:")
cur.execute("SELECT COUNT(*) as count FROM users")
user_count = cur.fetchone()['count']
print(f"  总用户数: {user_count}")

cur.execute("SELECT username, role, class_name FROM users")
users = cur.fetchall()
for user in users:
    print(f"  {user['username']} ({user['role']}) - {user['class_name']}")

conn.close()
print("\n✅ 数据库验证完成")
