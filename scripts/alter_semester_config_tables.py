#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
扩展学期配置表
添加周期类型相关字段，支持动态周期长度配置

新增字段：
1. default_period_type - 默认周期类型（新学期的初始配置）
2. current_period_type - 当前周期类型（可在学期中期变更）
"""

import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from classcomp.database import get_conn, put_conn

def alter_semester_config_tables():
    """为 semester_config 表添加周期类型字段"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        
        print(f"正在扩展学期配置表... (数据库类型: {'SQLite' if is_sqlite else 'PostgreSQL'})")
        
        # 检查字段是否已存在
        if is_sqlite:
            cur.execute("PRAGMA table_info(semester_config)")
            columns = [col[1] for col in cur.fetchall()]
        else:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'semester_config' AND table_schema = 'public'
            """)
            columns = [col['column_name'] if hasattr(col, 'keys') else col[0] for col in cur.fetchall()]
        
        fields_to_add = []
        
        if 'default_period_type' not in columns:
            fields_to_add.append('default_period_type')
        else:
            print("⚠️ default_period_type 字段已存在")
        
        if 'current_period_type' not in columns:
            fields_to_add.append('current_period_type')
        else:
            print("⚠️ current_period_type 字段已存在")
        
        if not fields_to_add:
            print("✅ 所有字段已存在，无需添加")
            return
        
        # 添加字段
        for field in fields_to_add:
            try:
                if is_sqlite:
                    # SQLite - 使用 ALTER TABLE ADD COLUMN
                    if field == 'default_period_type':
                        cur.execute("""
                            ALTER TABLE semester_config 
                            ADD COLUMN default_period_type TEXT DEFAULT 'biweekly' 
                            CHECK (default_period_type IN ('weekly', 'biweekly'))
                        """)
                    elif field == 'current_period_type':
                        cur.execute("""
                            ALTER TABLE semester_config 
                            ADD COLUMN current_period_type TEXT DEFAULT 'biweekly' 
                            CHECK (current_period_type IN ('weekly', 'biweekly'))
                        """)
                else:
                    # PostgreSQL - 使用 ALTER TABLE ADD COLUMN
                    if field == 'default_period_type':
                        cur.execute("""
                            ALTER TABLE semester_config 
                            ADD COLUMN default_period_type VARCHAR(20) DEFAULT 'biweekly' 
                            CHECK (default_period_type IN ('weekly', 'biweekly'))
                        """)
                    elif field == 'current_period_type':
                        cur.execute("""
                            ALTER TABLE semester_config 
                            ADD COLUMN current_period_type VARCHAR(20) DEFAULT 'biweekly' 
                            CHECK (current_period_type IN ('weekly', 'biweekly'))
                        """)
                
                print(f"✅ 成功添加字段: {field}")
            
            except Exception as e:
                # 字段可能已存在，或者其他错误
                print(f"⚠️ 添加字段 {field} 时出错: {e}")
        
        # 为现有的活跃学期设置默认值
        print("\n更新现有学期的周期类型...")
        placeholder = "?" if is_sqlite else "%s"
        
        try:
            cur.execute(f"""
                UPDATE semester_config 
                SET default_period_type = 'biweekly', 
                    current_period_type = 'biweekly'
                WHERE is_active = {placeholder} 
                  AND (default_period_type IS NULL OR current_period_type IS NULL)
            """, (1,))
            
            affected_rows = cur.rowcount
            if affected_rows > 0:
                print(f"✅ 更新了 {affected_rows} 个学期的周期类型")
            else:
                print("ℹ️ 没有需要更新的学期")
        except Exception as e:
            print(f"⚠️ 更新现有学期失败: {e}")
        
        # 提交更改
        conn.commit()
        print("\n✅ 学期配置表扩展完成")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 学期配置表扩展失败: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        put_conn(conn)

def verify_semester_config_schema():
    """验证学期配置表结构"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        print("\n=== 验证学期配置表结构 ===")
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        
        if is_sqlite:
            # SQLite - 使用 PRAGMA
            cur.execute("PRAGMA table_info(semester_config)")
            columns = cur.fetchall()
            
            print("\n学期配置表字段列表:")
            for col in columns:
                col_id = col[0]
                col_name = col[1]
                col_type = col[2]
                col_notnull = col[3]
                col_default = col[4]
                print(f"  {col_name} ({col_type}){' NOT NULL' if col_notnull else ''}{f' DEFAULT {col_default}' if col_default else ''}")
        else:
            # PostgreSQL - 使用 information_schema
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'semester_config' AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            print("\n学期配置表字段列表:")
            for col in columns:
                col_name = col['column_name'] if hasattr(col, 'keys') else col[0]
                col_type = col['data_type'] if hasattr(col, 'keys') else col[1]
                col_nullable = col['is_nullable'] if hasattr(col, 'keys') else col[2]
                col_default = col['column_default'] if hasattr(col, 'keys') else col[3]
                print(f"  {col_name} ({col_type}){' NOT NULL' if col_nullable == 'NO' else ''}{f' DEFAULT {col_default}' if col_default else ''}")
        
        # 检查关键字段是否存在
        column_names = []
        if is_sqlite:
            column_names = [col[1] for col in columns]
        else:
            column_names = [col['column_name'] if hasattr(col, 'keys') else col[0] for col in columns]
        
        required_fields = ['default_period_type', 'current_period_type']
        missing_fields = [field for field in required_fields if field not in column_names]
        
        if missing_fields:
            print(f"\n❌ 缺少字段: {', '.join(missing_fields)}")
        else:
            print("\n✅ 所有必需字段都已存在")
        
        # 查询活跃学期的周期类型配置
        placeholder = "?" if is_sqlite else "%s"
        cur.execute(f"""
            SELECT semester_name, default_period_type, current_period_type 
            FROM semester_config 
            WHERE is_active = {placeholder}
        """, (1,))
        active_semesters = cur.fetchall()
        
        if active_semesters:
            print("\n活跃学期的周期类型配置:")
            for semester in active_semesters:
                name = semester['semester_name'] if hasattr(semester, 'keys') else semester[0]
                default_type = semester['default_period_type'] if hasattr(semester, 'keys') else semester[1]
                current_type = semester['current_period_type'] if hasattr(semester, 'keys') else semester[2]
                print(f"  {name}: 默认={default_type}, 当前={current_type}")
        else:
            print("\n⚠️ 未找到活跃学期")
    
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        put_conn(conn)

if __name__ == "__main__":
    print("=" * 60)
    print("扩展学期配置表")
    print("=" * 60)
    
    alter_semester_config_tables()
    
    print("\n" + "=" * 60)
    print("验证表结构")
    print("=" * 60)
    
    verify_semester_config_schema()
    
    print("\n✅ 所有操作完成")