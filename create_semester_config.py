#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建学期设置表
用于存储学期配置信息：班级列表、周期设置等
"""

import sqlite3
import json
from datetime import datetime

def create_semester_tables():
    """创建学期配置相关的表"""
    conn = sqlite3.connect('classcomp.db')
    cur = conn.cursor()
    
    # 创建学期配置表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS semester_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester_name TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            first_period_end_date DATE NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建学期班级配置表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS semester_classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester_id INTEGER NOT NULL,
            grade_name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (semester_id) REFERENCES semester_config (id),
            UNIQUE(semester_id, class_name)
        )
    ''')
    
    # 检查是否有当前学期配置，如果没有则创建默认配置
    cur.execute('SELECT COUNT(*) FROM semester_config WHERE is_active = 1')
    if cur.fetchone()[0] == 0:
        print("创建默认学期配置...")
        
        # 创建默认学期配置
        cur.execute('''
            INSERT INTO semester_config (semester_name, start_date, first_period_end_date)
            VALUES (?, ?, ?)
        ''', ('2025年第一学期', '2025-07-01', '2025-07-27'))
        
        semester_id = cur.lastrowid
        
        # 创建默认班级配置
        default_classes = [
            ('中预', '中预1班'), ('中预', '中预2班'), ('中预', '中预3班'), ('中预', '中预4班'),
            ('中预', '中预5班'), ('中预', '中预6班'), ('中预', '中预7班'), ('中预', '中预8班'),
            ('初一', '初一1班'), ('初一', '初一2班'), ('初一', '初一3班'), ('初一', '初一4班'),
            ('初一', '初一5班'), ('初一', '初一6班'), ('初一', '初一7班'), ('初一', '初一8班'),
            ('初二', '初二1班'), ('初二', '初二2班'), ('初二', '初二3班'), ('初二', '初二4班'),
            ('初二', '初二5班'), ('初二', '初二6班'), ('初二', '初二7班'), ('初二', '初二8班'),
            ('高一', '高一1班'), ('高一', '高一2班'), ('高一', '高一3班'), ('高一', '高一4班'),
            ('高一', '高一5班'), ('高一', '高一6班'), ('高一', '高一7班'), ('高一', '高一8班'),
            ('高二', '高二1班'), ('高二', '高二2班'), ('高二', '高二3班'), ('高二', '高二4班'),
            ('高二', '高二5班'), ('高二', '高二6班'), ('高二', '高二7班'), ('高二', '高二8班'),
            ('高一VCE', '高一VCE'),
            ('高二VCE', '高二VCE'),
        ]
        
        for grade, class_name in default_classes:
            try:
                cur.execute('''
                    INSERT INTO semester_classes (semester_id, grade_name, class_name)
                    VALUES (?, ?, ?)
                ''', (semester_id, grade, class_name))
            except sqlite3.IntegrityError:
                # 班级已存在，跳过
                pass
        
        print(f"创建了默认学期配置，包含 {len(default_classes)} 个班级")
    
    conn.commit()
    conn.close()
    print("学期配置表创建完成")

def test_semester_config():
    """测试学期配置功能"""
    conn = sqlite3.connect('classcomp.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=== 当前学期配置 ===")
    cur.execute('''
        SELECT * FROM semester_config WHERE is_active = 1
    ''')
    semester = cur.fetchone()
    if semester:
        print(f"学期名称: {semester['semester_name']}")
        print(f"开始日期: {semester['start_date']}")
        print(f"第一周期结束: {semester['first_period_end_date']}")
        
        # 获取班级配置
        cur.execute('''
            SELECT grade_name, COUNT(*) as class_count
            FROM semester_classes 
            WHERE semester_id = ? AND is_active = 1
            GROUP BY grade_name
            ORDER BY grade_name
        ''', (semester['id'],))
        grades = cur.fetchall()
        
        print(f"\n班级配置:")
        total_classes = 0
        for grade in grades:
            print(f"  {grade['grade_name']}: {grade['class_count']}个班级")
            total_classes += grade['class_count']
        print(f"总计: {total_classes}个班级")
    else:
        print("未找到活跃的学期配置")
    
    conn.close()

if __name__ == "__main__":
    create_semester_tables()
    test_semester_config()
