#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建学期设置表                    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Shanghai'),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Shanghai'),用于存储学期配置信息：班级列表、周期设置等
"""

import os
import json
from datetime import datetime
from db import get_conn, put_conn

def create_semester_tables():
    """创建学期配置相关的表"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        
        print(f"正在创建学期配置表... (数据库类型: {'SQLite' if is_sqlite else 'PostgreSQL'})")
        
        if is_sqlite:
            # SQLite 版本 - 一次性创建所有表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS semester_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    semester_name TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT,
                    first_period_end_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            ''')
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS semester_classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    semester_id INTEGER NOT NULL,
                    grade_name TEXT NOT NULL,
                    class_name TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (semester_id) REFERENCES semester_config (id),
                    UNIQUE(semester_id, class_name)
                )
            ''')
        else:
            # PostgreSQL 版本 - 使用更兼容的语法
            cur.execute('''
                CREATE TABLE IF NOT EXISTS semester_config (
                    id SERIAL PRIMARY KEY,
                    semester_name VARCHAR(255) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    first_period_end_date DATE NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            ''')
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS semester_classes (
                    id SERIAL PRIMARY KEY,
                    semester_id INTEGER NOT NULL,
                    grade_name VARCHAR(255) NOT NULL,
                    class_name VARCHAR(255) NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Shanghai'),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Shanghai'),
                    FOREIGN KEY (semester_id) REFERENCES semester_config (id),
                    UNIQUE(semester_id, class_name)
                )
            ''')
        
        # 提交表结构创建
        conn.commit()
        print("✅ 学期配置表结构创建完成")
        
        # 检查是否需要创建默认数据
        cur.execute('SELECT COUNT(*) as count FROM semester_config WHERE is_active = 1')
        result = cur.fetchone()
        active_semester_count = result['count'] if hasattr(result, 'keys') else result[0]
        
        # 检查班级表是否为空
        cur.execute('SELECT COUNT(*) as count FROM semester_classes WHERE is_active = 1')
        result = cur.fetchone()
        active_class_count = result['count'] if hasattr(result, 'keys') else result[0]
        
        if active_semester_count == 0:
            print("📝 创建默认学期配置数据...")
            _create_default_semester_data(conn, cur, is_sqlite)
        elif active_class_count == 0:
            print("📝 学期配置存在但班级数据缺失，补充班级配置...")
            # 获取第一个活跃学期的ID
            cur.execute('SELECT id FROM semester_config WHERE is_active = 1 ORDER BY created_at LIMIT 1')
            semester_result = cur.fetchone()
            if semester_result:
                semester_id = semester_result['id'] if hasattr(semester_result, 'keys') else semester_result[0]
                _create_default_classes_for_semester(conn, cur, is_sqlite, semester_id)
                conn.commit()
            else:
                print("⚠️ 未找到活跃学期配置")
        else:
            print(f"✅ 已存在 {active_semester_count} 个活跃学期配置和 {active_class_count} 个班级配置")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 学期配置表创建失败: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        put_conn(conn)
    
    print("✅ 学期配置表创建完成")

def _create_default_classes_for_semester(conn, cur, is_sqlite, semester_id):
    """为指定学期创建默认班级配置的内部函数"""
    try:
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
        
        # 批量插入班级配置
        if is_sqlite:
            placeholder_sql = 'INSERT OR IGNORE INTO semester_classes (semester_id, grade_name, class_name) VALUES (?, ?, ?)'
        else:
            placeholder_sql = 'INSERT INTO semester_classes (semester_id, grade_name, class_name) VALUES (%s, %s, %s) ON CONFLICT (semester_id, class_name) DO NOTHING'
        
        inserted_count = 0
        for grade, class_name in default_classes:
            try:
                cur.execute(placeholder_sql, (semester_id, grade, class_name))
                if cur.rowcount > 0:
                    inserted_count += 1
            except Exception as e:
                # 班级已存在或其他错误，记录但继续
                print(f"⚠️ 跳过班级 {class_name}: {e}")
        
        print(f"✅ 为学期 {semester_id} 创建了 {inserted_count}/{len(default_classes)} 个班级配置")
        
    except Exception as e:
        print(f"❌ 班级配置创建失败: {e}")
        raise e

def _create_default_semester_data(conn, cur, is_sqlite):
    """创建默认学期配置数据的内部函数"""
    try:
        # 插入默认学期配置
        if is_sqlite:
            cur.execute('''
                INSERT INTO semester_config (semester_name, start_date, first_period_end_date)
                VALUES (?, ?, ?)
            ''', ('2025年第一学期', '2025-07-01', '2025-07-27'))
            semester_id = cur.lastrowid
        else:
            # PostgreSQL - 使用 RETURNING 子句获取ID
            cur.execute('''
                INSERT INTO semester_config (semester_name, start_date, first_period_end_date)
                VALUES (%s, %s, %s) RETURNING id
            ''', ('2025年第一学期', '2025-07-01', '2025-07-27'))
            result = cur.fetchone()
            semester_id = result['id'] if hasattr(result, 'keys') else result[0]
        
        # 创建默认班级配置
        _create_default_classes_for_semester(conn, cur, is_sqlite, semester_id)
        
        # 提交所有更改
        conn.commit()
        print(f"✅ 创建了默认学期配置")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 默认学期配置数据创建失败: {e}")
        raise e

def create_default_semester_config():
    """创建默认学期配置（独立函数，不依赖表创建）"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        
        print(f"检查学期配置数据... (数据库类型: {'SQLite' if is_sqlite else 'PostgreSQL'})")
        
        # 检查是否有当前学期配置
        cur.execute('SELECT COUNT(*) FROM semester_config WHERE is_active = 1')
        active_count = cur.fetchone()[0]
        
        if active_count == 0:
            print("📝 创建默认学期配置数据...")
            _create_default_semester_data(conn, cur, is_sqlite)
        else:
            print(f"✅ 已存在 {active_count} 个活跃学期配置，跳过创建")
                
    except Exception as e:
        print(f"❌ 默认学期配置检查失败: {e}")
        raise e
    finally:
        put_conn(conn)

def test_semester_config():
    """测试学期配置功能"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        
        print("=== 当前学期配置 ===")
        cur.execute('SELECT * FROM semester_config WHERE is_active = 1')
        semester = cur.fetchone()
        
        if semester:
            print(f"学期名称: {semester['semester_name']}")
            print(f"开始日期: {semester['start_date']}")
            print(f"第一周期结束: {semester['first_period_end_date']}")
            
            # 获取班级配置，使用统一的SQL语法
            if is_sqlite:
                cur.execute('''
                    SELECT grade_name, COUNT(*) as class_count
                    FROM semester_classes 
                    WHERE semester_id = ? AND is_active = 1
                    GROUP BY grade_name
                    ORDER BY 
                        CASE grade_name 
                            WHEN '中预' THEN 1
                            WHEN '初一' THEN 2
                            WHEN '初二' THEN 3
                            WHEN '高一' THEN 4
                            WHEN '高二' THEN 5
                            WHEN '高一VCE' THEN 6
                            WHEN '高二VCE' THEN 7
                            ELSE 99
                        END
                ''', (semester['id'],))
            else:
                cur.execute('''
                    SELECT grade_name, COUNT(*) as class_count
                    FROM semester_classes 
                    WHERE semester_id = %s AND is_active = 1
                    GROUP BY grade_name
                    ORDER BY 
                        CASE grade_name 
                            WHEN '中预' THEN 1
                            WHEN '初一' THEN 2
                            WHEN '初二' THEN 3
                            WHEN '高一' THEN 4
                            WHEN '高二' THEN 5
                            WHEN '高一VCE' THEN 6
                            WHEN '高二VCE' THEN 7
                            ELSE 99
                        END
                ''', (semester['id'],))
            
            grades = cur.fetchall()
            
            if grades:
                print(f"\n班级配置:")
                total_classes = 0
                for grade in grades:
                    grade_name = grade['grade_name'] if hasattr(grade, 'keys') else grade[0]
                    class_count = grade['class_count'] if hasattr(grade, 'keys') else grade[1]
                    print(f"  {grade_name}: {class_count}个班级")
                    total_classes += class_count
                print(f"总计: {total_classes}个班级")
            else:
                print("⚠️ 未找到班级配置")
        else:
            print("❌ 未找到活跃的学期配置")
    
    except Exception as e:
        print(f"❌ 学期配置测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        put_conn(conn)

if __name__ == "__main__":
    create_semester_tables()
    test_semester_config()
