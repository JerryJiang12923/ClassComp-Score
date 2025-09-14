#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试班级排序逻辑
"""

import sqlite3
import os

def debug_class_sorting():
    """调试班级排序逻辑"""
    # 创建临时数据库进行调试
    test_db = 'debug_sorting.db'
    
    try:
        # 创建测试数据库
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # 创建测试表
        cur.execute('''
            CREATE TABLE test_classes (
                class_name TEXT
            )
        ''')
        
        # 插入测试数据
        test_classes = ['中预1班', '中预2班', '中预9班', '中预10班']
        
        for class_name in test_classes:
            cur.execute('INSERT INTO test_classes (class_name) VALUES (?)', (class_name,))
        
        conn.commit()
        
        print("调试班级名称提取逻辑:")
        
        # 测试数字提取逻辑
        cur.execute('''
            SELECT 
                class_name,
                substr(class_name, -2, 1) as second_last_char,
                substr(class_name, -1, 1) as last_char,
                substr(class_name, -2, 2) as last_two_chars,
                CASE 
                    WHEN substr(class_name, -2, 1) IN ('0','1','2','3','4','5','6','7','8','9') 
                    AND substr(class_name, -1, 1) IN ('0','1','2','3','4','5','6','7','8','9')
                    THEN CAST(substr(class_name, -2, 2) AS INTEGER)
                    WHEN substr(class_name, -1, 1) IN ('0','1','2','3','4','5','6','7','8','9')
                    THEN CAST(substr(class_name, -1, 1) AS INTEGER)
                    ELSE 0
                END as extracted_number
            FROM test_classes
            ORDER BY class_name
        ''')
        
        results = cur.fetchall()
        
        for row in results:
            print(f"{row['class_name']:8} | 倒数第二字符: '{row['second_last_char']}' | 最后字符: '{row['last_char']}' | 最后两字符: '{row['last_two_chars']}' | 提取数字: {row['extracted_number']}")
        
    except Exception as e:
        print(f"调试出错: {e}")
    finally:
        # 清理测试数据库
        conn.close()
        if os.path.exists(test_db):
            os.remove(test_db)

if __name__ == '__main__':
    debug_class_sorting()
