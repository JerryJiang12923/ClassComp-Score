#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据迁移脚本：将现有评分数据的隐式周期信息转换为显式的 period_metadata 记录

迁移策略：
1. 扫描 scores 表中所有唯一的评分日期
2. 使用现有的 calculate_period_info() 逻辑计算每个日期的周期信息
3. 将周期信息插入 period_metadata 表
4. 标记所有迁移的周期类型为 'biweekly'（因为现有数据都是14天周期）
5. 验证数据完整性
"""

import os
import sys
from datetime import datetime, date, timedelta

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from classcomp.database import get_conn, put_conn
from classcomp.utils.period_utils import calculate_period_info, get_current_semester_config

def migrate_existing_periods_to_metadata():
    """
    将现有评分数据的隐式周期信息转换为显式的 period_metadata 记录
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        print("=" * 60)
        print("开始迁移现有周期数据到 period_metadata 表")
        print("=" * 60)
        
        # 1. 获取活跃学期配置
        semester_config = get_current_semester_config(conn)
        if not semester_config:
            print("❌ 未找到活跃学期配置，无法迁移")
            return False
        
        semester = semester_config['semester']
        semester_id = semester['id']
        semester_name = semester['semester_name']
        
        print(f"\n找到活跃学期: {semester_name} (ID: {semester_id})")
        print(f"学期开始日期: {semester['start_date']}")
        print(f"第一周期结束日期: {semester['first_period_end_date']}")
        
        # 2. 获取所有评分记录的创建日期（去重）
        print("\n正在扫描评分记录...")
        
        if is_sqlite:
            cur.execute("""
                SELECT DISTINCT DATE(created_at) as score_date 
                FROM scores 
                ORDER BY score_date
            """)
        else:
            cur.execute("""
                SELECT DISTINCT DATE(created_at AT TIME ZONE 'Asia/Shanghai') as score_date 
                FROM scores 
                ORDER BY score_date
            """)
        
        unique_dates = cur.fetchall()
        date_list = [row['score_date'] if hasattr(row, 'keys') else row[0] for row in unique_dates]
        
        if not date_list:
            print("ℹ️ 未找到评分记录，无需迁移")
            return True
        
        print(f"找到 {len(date_list)} 个唯一的评分日期")
        print(f"日期范围: {date_list[0]} ~ {date_list[-1]}")
        
        # 3. 为每个日期计算周期信息并插入 period_metadata
        print("\n开始计算和迁移周期信息...")
        
        migrated_periods = {}  # 使用字典避免重复：{period_number: period_info}
        
        for date_str in date_list:
            # 将字符串转换为 date 对象
            if isinstance(date_str, str):
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                target_date = date_str
            
            # 使用现有逻辑计算周期
            try:
                period_info = calculate_period_info(
                    target_date=target_date,
                    semester_config=semester,
                    conn=conn
                )
                
                period_number = period_info['period_number']
                
                # 避免重复处理同一周期
                if period_number in migrated_periods:
                    continue
                
                # 记录周期信息
                migrated_periods[period_number] = {
                    'number': period_number,
                    'start': period_info['period_start'],
                    'end': period_info['period_end']
                }
                
            except Exception as e:
                print(f"⚠️ 计算日期 {date_str} 的周期信息失败: {e}")
                continue
        
        print(f"识别出 {len(migrated_periods)} 个不同的周期")
        
        # 4. 批量插入 period_metadata
        print("\n开始插入周期元数据...")
        
        inserted_count = 0
        skipped_count = 0
        
        for period_number in sorted(migrated_periods.keys()):
            period = migrated_periods[period_number]
            
            try:
                # 检查是否已存在
                cur.execute(f"""
                    SELECT id FROM period_metadata 
                    WHERE semester_id = {placeholder} AND period_number = {placeholder}
                """, (semester_id, period_number))
                
                existing = cur.fetchone()
                
                if existing:
                    skipped_count += 1
                    print(f"  周期 {period_number}: 已存在，跳过")
                    continue
                
                # 插入新周期
                if is_sqlite:
                    cur.execute("""
                        INSERT INTO period_metadata 
                        (semester_id, period_number, period_type, start_date, end_date, created_by)
                        VALUES (?, ?, 'biweekly', ?, ?, 'migration_script')
                    """, (
                        semester_id,
                        period_number,
                        period['start'].strftime('%Y-%m-%d'),
                        period['end'].strftime('%Y-%m-%d')
                    ))
                else:
                    cur.execute("""
                        INSERT INTO period_metadata 
                        (semester_id, period_number, period_type, start_date, end_date, created_by)
                        VALUES (%s, %s, 'biweekly', %s, %s, 'migration_script')
                    """, (
                        semester_id,
                        period_number,
                        period['start'],
                        period['end']
                    ))
                
                inserted_count += 1
                print(f"  ✅ 周期 {period_number}: {period['start']} ~ {period['end']}")
                
            except Exception as e:
                print(f"  ❌ 周期 {period_number} 插入失败: {e}")
        
        # 5. 提交事务
        conn.commit()
        
        print(f"\n迁移完成:")
        print(f"  成功插入: {inserted_count} 个周期")
        print(f"  已存在跳过: {skipped_count} 个周期")
        
        # 6. 验证数据完整性
        print("\n验证数据完整性...")
        verify_migration(conn, semester_id)
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        put_conn(conn)

def verify_migration(conn, semester_id):
    """验证迁移后的数据完整性"""
    try:
        cur = conn.cursor()
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        # 1. 检查 period_metadata 表中的记录数
        cur.execute(f"""
            SELECT COUNT(*) as count FROM period_metadata 
            WHERE semester_id = {placeholder}
        """, (semester_id,))
        
        metadata_count = cur.fetchone()
        count = metadata_count['count'] if hasattr(metadata_count, 'keys') else metadata_count[0]
        print(f"✅ period_metadata 表中有 {count} 条周期记录")
        
        # 2. 检查周期的连续性（无间隙）
        cur.execute(f"""
            SELECT period_number, start_date, end_date 
            FROM period_metadata 
            WHERE semester_id = {placeholder}
            ORDER BY period_number
        """, (semester_id,))
        
        periods = cur.fetchall()
        
        if len(periods) > 1:
            has_gap = False
            for i in range(len(periods) - 1):
                current = periods[i]
                next_period = periods[i + 1]
                
                current_end = current['end_date'] if hasattr(current, 'keys') else current[2]
                next_start = next_period['start_date'] if hasattr(next_period, 'keys') else next_period[1]
                
                # 转换为 date 对象进行比较
                if isinstance(current_end, str):
                    current_end = datetime.strptime(current_end, '%Y-%m-%d').date()
                if isinstance(next_start, str):
                    next_start = datetime.strptime(next_start, '%Y-%m-%d').date()
                
                # 下一周期的开始应该是当前周期结束的下一天
                expected_next_start = current_end + timedelta(days=1)
                
                if next_start != expected_next_start:
                    has_gap = True
                    print(f"⚠️ 周期 {i} 和 {i+1} 之间存在间隙或重叠")
                    print(f"   周期 {i} 结束: {current_end}")
                    print(f"   周期 {i+1} 开始: {next_start}")
            
            if not has_gap:
                print("✅ 周期边界连续，无间隙或重叠")
        
        # 3. 检查所有评分记录是否都能匹配到周期
        print("\n检查评分记录的周期归属...")
        
        if is_sqlite:
            cur.execute("""
                SELECT COUNT(*) as count FROM scores
            """)
        else:
            cur.execute("""
                SELECT COUNT(*) as count FROM scores
            """)
        
        scores_result = cur.fetchone()
        total_scores = scores_result['count'] if hasattr(scores_result, 'keys') else scores_result[0]
        
        if total_scores > 0:
            # 检查有多少评分记录的日期在周期范围内
            if is_sqlite:
                cur.execute(f"""
                    SELECT COUNT(DISTINCT s.id) as matched_count
                    FROM scores s
                    INNER JOIN period_metadata p ON 
                        DATE(s.created_at) BETWEEN p.start_date AND p.end_date
                        AND p.semester_id = {placeholder}
                """, (semester_id,))
            else:
                cur.execute(f"""
                    SELECT COUNT(DISTINCT s.id) as matched_count
                    FROM scores s
                    INNER JOIN period_metadata p ON 
                        DATE(s.created_at AT TIME ZONE 'Asia/Shanghai') BETWEEN p.start_date AND p.end_date
                        AND p.semester_id = {placeholder}
                """, (semester_id,))
            
            matched_result = cur.fetchone()
            matched_count = matched_result['matched_count'] if hasattr(matched_result, 'keys') else matched_result[0]
            
            coverage_rate = (matched_count / total_scores * 100) if total_scores > 0 else 0
            
            print(f"  总评分记录: {total_scores}")
            print(f"  匹配到周期: {matched_count}")
            print(f"  覆盖率: {coverage_rate:.2f}%")
            
            if coverage_rate < 100:
                print(f"  ⚠️ 有 {total_scores - matched_count} 条评分记录未匹配到周期")
            else:
                print("  ✅ 所有评分记录都已匹配到周期")
        else:
            print("  ℹ️ 没有评分记录")
        
    except Exception as e:
        print(f"验证过程出错: {e}")
        import traceback
        traceback.print_exc()

def rollback_migration():
    """回滚迁移：删除所有由迁移脚本创建的 period_metadata 记录"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        print("=" * 60)
        print("开始回滚迁移")
        print("=" * 60)
        
        # 删除由迁移脚本创建的记录
        cur.execute(f"""
            DELETE FROM period_metadata 
            WHERE created_by = {placeholder}
        """, ('migration_script',))
        
        deleted_count = cur.rowcount
        conn.commit()
        
        print(f"✅ 已删除 {deleted_count} 条迁移记录")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 回滚失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        put_conn(conn)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        # 回滚模式
        print("\n⚠️ 警告：这将删除所有迁移的周期元数据！")
        confirm = input("确认要回滚吗？(yes/no): ")
        if confirm.lower() == 'yes':
            rollback_migration()
        else:
            print("已取消回滚")
    else:
        # 正常迁移模式
        success = migrate_existing_periods_to_metadata()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ 数据迁移成功完成")
            print("=" * 60)
            print("\n提示:")
            print("  - 所有历史周期已转换为 period_metadata 记录")
            print("  - 周期类型统一标记为 'biweekly'")
            print("  - 如需回滚，请运行: python migrate_existing_periods.py --rollback")
        else:
            print("\n" + "=" * 60)
            print("❌ 数据迁移失败")
            print("=" * 60)
            sys.exit(1)