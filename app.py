# app.py

from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('score.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        评分人姓名 TEXT NOT NULL,
        信息委员班级 TEXT NOT NULL,
        被查年级 TEXT NOT NULL,
        被查班级 TEXT NOT NULL,
        分项1 INTEGER DEFAULT 3,
        分项2 INTEGER DEFAULT 3,
        分项3 INTEGER DEFAULT 4,
        总分 INTEGER DEFAULT 10,
        备注 TEXT,
        提交时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_scores', methods=['POST'])
def submit_scores():
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, message="无效的请求数据"), 400
        
        required_fields = ['name', 'info_class', 'checked_grade', 'scores']
        if not all(field in data for field in required_fields):
            return jsonify(success=False, message="缺少必要字段"), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for score_data in data['scores']:
            cursor.execute('''
                INSERT INTO scores (
                    评分人姓名, 信息委员班级, 被查年级, 被查班级, 
                    分项1, 分项2, 分项3, 总分, 备注
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['name'],
                data['info_class'],
                data['checked_grade'],
                score_data['className'],
                score_data['score1'],
                score_data['score2'],
                score_data['score3'],
                score_data['total'],
                score_data.get('note', '')
            ))
        
        conn.commit()
        return jsonify(success=True)
    
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    
    finally:
        conn.close()

if __name__ == '__main__':
    create_table()
    app.run(debug=True)