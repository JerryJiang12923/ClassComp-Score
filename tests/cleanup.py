#!/usr/bin/env python3
"""清理测试数据和数据库"""
import os
import sqlite3
import glob

def cleanup_database():
    """清理数据库"""
    db_files = ['classcomp.db', 'classcomp.db-journal', 'classcomp.db-wal', 'classcomp.db-shm']
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"已删除: {db_file}")

def cleanup_exports():
    """清理导出的文件"""
    export_files = glob.glob('exports/*.xlsx')
    for file in export_files:
        os.remove(file)
        print(f"已删除: {file}")
    
    if os.path.exists('exports') and not os.listdir('exports'):
        os.rmdir('exports')
        print("已清理空exports目录")

def cleanup_test_files():
    """清理测试文件"""
    test_files = [
        '测试评分表_*.xlsx',
        '评分表_*.xlsx',
        'test_*.db',
    ]
    
    for pattern in test_files:
        files = glob.glob(pattern)
        for file in files:
            os.remove(file)
            print(f"已删除: {file}")

if __name__ == "__main__":
    print("=== 开始清理测试数据 ===")
    cleanup_database()
    cleanup_exports()
    cleanup_test_files()
    print("=== 清理完成 ===")