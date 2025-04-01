# query_lib.py

import sqlite3

def get_db_connection():
    conn = sqlite3.connect('score.db')
    conn.row_factory = sqlite3.Row
    return conn

def query_scores(grade, class_num):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM scores WHERE 年级 = ? AND 班级 = ?", (grade, class_num))
    results = cursor.fetchall()
    
    conn.close()
    return results