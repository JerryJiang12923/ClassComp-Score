#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建评分周期元数据表
用于支持动态周期长度配置和历史数据完整性

表结构：
1. period_metadata - 存储每个周期的具体配置信息
2. period_config_history - 记录周期配置变更历史
"""

import os
import sys
from datetime import datetime

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from classcomp.database import get_conn, put_conn

def create_period_metadata_tables():
    """创建周期元数据相关表"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        
        print(f"正在创建周期元数据表... (数据库类型: {'SQLite' if is_sqlite else 'PostgreSQL'})")
        
        if is_sqlite:
            # SQLite 版本 - 周期元数据表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS period_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    semester_id INTEGER NOT NULL,
                    period_number INTEGER NOT NULL,
                    period_type TEXT NOT NULL CHECK (period_type IN ('weekly', 'biweekly')),
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    created_by TEXT,
                    FOREIGN KEY (semester_id) REFERENCES semester_config(id) ON DELETE CASCADE,
                    UNIQUE(semester_id, period_number)
                )
            ''')
            
            # SQLite 版本 - 配置变更历史表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS period_config_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    semester_id INTEGER NOT NULL,
                    config_type TEXT NOT NULL CHECK (config_type IN ('weekly', 'biweekly')),
                    effective_from_period INTEGER NOT NULL,
                    effective_from_date TEXT NOT NULL,
                    changed_at TEXT DEFAULT (datetime('now')),
                    changed_by TEXT,
                    reason TEXT,
                    FOREIGN KEY (semester_id) REFERENCES semester_config(id) ON DELETE CASCADE
                )
            ''')
        else:
            # PostgreSQL 版本 - 周期元数据表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS period_metadata (
                    id SERIAL PRIMARY KEY,
                    semester_id INTEGER NOT NULL,
                    period_number INTEGER NOT NULL,
                    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('weekly', 'biweekly')),
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    created_by VARCHAR(100),
                    FOREIGN KEY (semester_id) REFERENCES semester_config(id) ON DELETE CASCADE,
                    UNIQUE(semester_id, period_number)
                )
            ''')
            
            # PostgreSQL 版本 - 配置变更历史表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS period_config_history (
                    id SERIAL PRIMARY KEY,
                    semester_id INTEGER NOT NULL,
                    config_type VARCHAR(20) NOT NULL CHECK (config_type IN ('weekly', 'biweekly')),
                    effective_from_period INTEGER NOT NULL,
                    effective_from_date DATE NOT NULL,
                    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    changed_by VARCHAR(100),
                    reason TEXT,
                    FOREIGN KEY (semester_id) REFERENCES semester_config(id) ON DELETE CASCADE
                )
            ''')
        
        # 创建索引优化查询性能
        print("创建索引...")
        
        indexes = [
            # period_metadata 表索引
            "CREATE INDEX IF NOT EXISTS idx_period_metadata_semester ON period_metadata(semester_id)",
            "CREATE INDEX IF NOT EXISTS idx_period_metadata_dates ON period_metadata(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_period_metadata_period_number ON period_metadata(period_number)",
            "CREATE INDEX IF NOT EXISTS idx_period_metadata_active ON period_metadata(is_active)",
            
            # period_config_history 表索引
            "CREATE INDEX IF NOT EXISTS idx_period_config_semester ON period_config_history(semester_id)",
            "CREATE INDEX IF NOT EXISTS idx_period_config_date ON period_config_history(changed_at)"
        ]
        
        for index_sql in indexes:
            cur.execute(index_sql)
        
        # 提交表结构创建
        conn.commit()
        print("✅ 周期元数据表结构创建完成")
        
        # 验证表是否创建成功
        if is_sqlite:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('period_metadata', 'period_config_history')")
        else:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name IN ('period_metadata', 'period_config_history') AND table_schema='public'")
        
        tables = cur.fetchall()
        table_names = [t['name'] if is_sqlite else t['table_name'] for t in tables]
        
        if 'period_metadata' in table_names:
            print("✅ period_metadata 表创建成功")
        else:
            print("❌ period_metadata 表创建失败")
        
        if 'period_config_history' in table_names:
            print("✅ period_config_history 表创建成功")
        else:
            print("❌ period_config_history 表创建失败")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 周期元数据表创建失败: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        put_conn(conn)
    
    print("✅ 周期元数据表创建完成")

def test_period_metadata_tables():
    """测试周期元数据表功能"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        print("\n=== 测试周期元数据表 ===")
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        # 1. 查询是否有活跃学期
        cur.execute(f'SELECT id, semester_name FROM semester_config WHERE is_active = {placeholder}', (1,))
        semester = cur.fetchone()
        
        if not semester:
            print("⚠️ 未找到活跃学期，跳过测试数据插入")
            return
        
        semester_id = semester['id'] if hasattr(semester, 'keys') else semester[0]
        semester_name = semester['semester_name'] if hasattr(semester, 'keys') else semester[1]
        print(f"找到活跃学期: {semester_name} (ID: {semester_id})")
        
        # 2. 测试插入周期元数据
        print("\n测试插入周期元数据...")
        test_data = {
            'semester_id': semester_id,
            'period_number': 0,
            'period_type': 'biweekly',
            'start_date': '2025-07-01',
            'end_date': '2025-07-27',
            'created_by': 'test_script'
        }
        
        try:
            if is_sqlite:
                cur.execute('''
                    INSERT OR IGNORE INTO period_metadata 
                    (semester_id, period_number, period_type, start_date, end_date, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (test_data['semester_id'], test_data['period_number'], test_data['period_type'],
                      test_data['start_date'], test_data['end_date'], test_data['created_by']))
            else:
                cur.execute('''
                    INSERT INTO period_metadata 
                    (semester_id, period_number, period_type, start_date, end_date, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (semester_id, period_number) DO NOTHING
                ''', (test_data['semester_id'], test_data['period_number'], test_data['period_type'],
                      test_data['start_date'], test_data['end_date'], test_data['created_by']))
            
            conn.commit()
            print("✅ 测试数据插入成功")
        except Exception as e:
            print(f"⚠️ 测试数据插入失败（可能已存在）: {e}")
        
        # 3. 查询周期元数据
        cur.execute(f'''
            SELECT period_number, period_type, start_date, end_date, created_by 
            FROM period_metadata 
            WHERE semester_id = {placeholder}
            ORDER BY period_number
        ''', (semester_id,))
        periods = cur.fetchall()
        
        if periods:
            print(f"\n找到 {len(periods)} 个周期记录:")
            for period in periods:
                period_num = period['period_number'] if hasattr(period, 'keys') else period[0]
                period_type = period['period_type'] if hasattr(period, 'keys') else period[1]
                start_date = period['start_date'] if hasattr(period, 'keys') else period[2]
                end_date = period['end_date'] if hasattr(period, 'keys') else period[3]
                print(f"  周期 {period_num}: {period_type} ({start_date} ~ {end_date})")
        else:
            print("⚠️ 未找到周期记录")
        
        # 4. 测试配置变更历史表
        print("\n测试配置变更历史表...")
        try:
            if is_sqlite:
                cur.execute('''
                    INSERT INTO period_config_history 
                    (semester_id, config_type, effective_from_period, effective_from_date, changed_by, reason)
                    VALUES (?, 'biweekly', 0, '2025-07-01', 'test_script', '初始化测试')
                ''', (semester_id,))
            else:
                cur.execute('''
                    INSERT INTO period_config_history 
                    (semester_id, config_type, effective_from_period, effective_from_date, changed_by, reason)
                    VALUES (%s, 'biweekly', 0, '2025-07-01', 'test_script', '初始化测试')
                ''', (semester_id,))
            
            conn.commit()
            print("✅ 配置变更历史插入成功")
        except Exception as e:
            print(f"⚠️ 配置变更历史插入失败: {e}")
        
        # 5. 查询配置变更历史
        cur.execute(f'''
            SELECT config_type, effective_from_period, changed_at, changed_by, reason
            FROM period_config_history 
            WHERE semester_id = {placeholder}
            ORDER BY changed_at DESC
        ''', (semester_id,))
        history = cur.fetchall()
        
        if history:
            print(f"\n找到 {len(history)} 条配置变更记录:")
            for record in history:
                config_type = record['config_type'] if hasattr(record, 'keys') else record[0]
                effective_from = record['effective_from_period'] if hasattr(record, 'keys') else record[1]
                changed_at = record['changed_at'] if hasattr(record, 'keys') else record[2]
                changed_by = record['changed_by'] if hasattr(record, 'keys') else record[3]
                reason = record['reason'] if hasattr(record, 'keys') else record[4]
                print(f"  {changed_at}: 变更为 {config_type} (从周期{effective_from}生效)")
                if reason:
                    print(f"    原因: {reason}")
        else:
            print("⚠️ 未找到配置变更记录")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        put_conn(conn)

if __name__ == "__main__":
    print("=" * 60)
    print("创建周期元数据表")
    print("=" * 60)
    
    create_period_metadata_tables()
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    test_period_metadata_tables()
    
    print("\n✅ 所有操作完成")