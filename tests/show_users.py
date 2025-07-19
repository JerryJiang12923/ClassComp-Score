#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('classcomp.db')
conn.row_factory = sqlite3.Row

print("=== 全量测试用户列表 ===")
print(f"总用户数: {conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]}")
print(f"总评分数: {conn.execute('SELECT COUNT(*) FROM scores').fetchone()[0]}")
print()

print("管理员用户:")
admin = conn.execute("SELECT username, class_name FROM users WHERE role='admin'").fetchone()
print(f"  {admin['username']} - {admin['class_name']}")

print("\n教师用户:")
teachers = conn.execute("SELECT username, class_name FROM users WHERE role='teacher' ORDER BY username").fetchall()
for teacher in teachers:
    print(f"  {teacher['username']} - {teacher['class_name']}")

print("\n学生用户 (按年级分类):")
for grade in ['中预', '初一', '初二', '高一', '高二']:
    students = conn.execute("""
        SELECT username, class_name FROM users 
        WHERE role='student' AND class_name LIKE ? 
        ORDER BY class_name, username
    """, (f'{grade}%',)).fetchall()
    print(f"\n{grade}年级 ({len(students)}人):")
    for student in students[:6]:  # 显示前6个
        print(f"  {student['username']} - {student['class_name']}")
    if len(students) > 6:
        print(f"  ... 还有{len(students)-6}人")

print("\n=== 评分链验证 ===")
for grade in ['中预', '初一', '初二', '高一', '高二']:
    scores = conn.execute("SELECT COUNT(*) FROM scores WHERE target_grade=?", (grade,)).fetchone()[0]
    classes = conn.execute("SELECT COUNT(DISTINCT target_class) FROM scores WHERE target_grade=?", (grade,)).fetchone()[0]
    total_classes = len([c for c in conn.execute("SELECT DISTINCT class_name FROM users WHERE role='student'").fetchall() if c[0].startswith(grade)])
    print(f"{grade}: {scores}条评分, {classes}/{total_classes}班级覆盖")

conn.close()