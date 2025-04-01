# -*- coding: utf-8 -*-
import sqlite3

# 连接数据库（如果不存在会自动创建）
db = sqlite3.connect('score.db')
cursor = db.cursor()

def create_table():
    # 执行建表语句
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                年级 TEXT CHECK(年级 IN ('中预','初一','初二','初三','高一','高二','高三')),
                班级 INTEGER,
                月份 TEXT,
                分数 INTEGER)''')

def finish():
    # 提交并关闭
    db.commit()
    db.close()

def insert_data():
    # 插入数据，明确指定列名
    cursor.execute("INSERT INTO scores (年级, 班级, 月份, 分数) VALUES ('高一', 5, '2024-03', 88)")
    db.commit()  # 提交更改

def query():
    # 查询数据
    cursor.execute("SELECT * FROM scores") 
    results = cursor.fetchall()  # 获取所有结果
    count = 0
    for row in results:
        count += 1
        print(row)  # 打印每一行
    return count

def replace_data():
    cursor.execute('''UPDATE scores
    SET 年级 = '高二'
    WHERE 班级 = 5;''')
    db.commit()  # 提交更改

def delete_data():
    cursor.execute('''DELETE FROM scores
    WHERE id = 1;''')
    db.commit()  # 提交更改

create_table()
insert_data()
query()