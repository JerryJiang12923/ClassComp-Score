#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""数据库迁移脚本 - 添加软删除字段"""

import os
import sqlite3
from datetime import datetime

def migrate_database():
    """为现有数据库添加软删除字段"""
    
    db_path = "classcomp.db"
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在，请先运行应用程序")
        return False
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        cur = conn.cursor()
        
        print("🔄 开始数据库迁移...")
        
        # 检查当前表结构
        cur.execute("PRAGMA table_info(scores)")
        columns = [column[1] for column in cur.fetchall()]
        
        print(f"📊 当前 scores 表字段: {', '.join(columns)}")
        
        # 添加 is_active 字段
        if 'is_active' not in columns:
            print("➕ 添加 is_active 字段...")
            cur.execute("ALTER TABLE scores ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            
            # 将所有现有记录标记为活跃
            cur.execute("UPDATE scores SET is_active = 1 WHERE is_active IS NULL")
            print("✅ is_active 字段添加成功，所有现有记录已标记为活跃")
        else:
            print("✅ is_active 字段已存在")
        
        # 添加 replaced_by 字段
        if 'replaced_by' not in columns:
            print("➕ 添加 replaced_by 字段...")
            cur.execute("ALTER TABLE scores ADD COLUMN replaced_by INTEGER")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_scores_replaced_by ON scores(replaced_by)")
            print("✅ replaced_by 字段添加成功")
        else:
            print("✅ replaced_by 字段已存在")
        
        # 添加索引
        print("📊 添加性能优化索引...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scores_is_active ON scores(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_scores_user_active ON scores(user_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_scores_period_active ON scores(target_grade, target_class, is_active)"
        ]
        
        for index_sql in indexes:
            cur.execute(index_sql)
        
        print("✅ 索引添加完成")
        
        # 验证迁移结果
        cur.execute("PRAGMA table_info(scores)")
        new_columns = [column[1] for column in cur.fetchall()]
        print(f"📊 迁移后 scores 表字段: {', '.join(new_columns)}")
        
        # 统计数据
        cur.execute("SELECT COUNT(*) as total FROM scores")
        total = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as active FROM scores WHERE is_active = 1")
        active = cur.fetchone()['active']
        
        print(f"📈 数据统计: 总记录 {total} 条，活跃记录 {active} 条")
        
        conn.commit()
        print("🎉 数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 开始数据库迁移...")
    success = migrate_database()
    if success:
        print("\n✅ 迁移成功！现在可以使用软删除功能了。")
    else:
        print("\n❌ 迁移失败，请检查错误信息。")
