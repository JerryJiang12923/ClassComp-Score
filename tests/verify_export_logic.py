#!/usr/bin/env python3
"""
验证Excel导出功能是否正确处理管理员记录
"""
import pandas as pd
from datetime import datetime, timedelta
from db import get_conn, put_conn
import os

def verify_export_logic():
    """验证导出逻辑"""
    month = "2025-07"
    conn = get_conn()
    
    try:
        cur = conn.cursor()
        placeholder = "?"
        
        print(f"🔍 验证{month}月份Excel导出逻辑")
        
        # 1. 获取原始数据
        sql = f"""
            SELECT
              id, evaluator_name, evaluator_class, target_grade, target_class,
              score1, score2, score3, total, note, created_at
            FROM scores
            WHERE strftime('%Y-%m', created_at) = {placeholder}
            ORDER BY target_grade, target_class, evaluator_class, created_at
        """
        cur.execute(sql, (month,))
        rows = cur.fetchall()
        
        if not rows:
            print("❌ 当月无数据")
            return False
            
        print(f"📊 原始数据: {len(rows)}条")
        
        # 2. 创建DataFrame并处理
        df = pd.DataFrame(rows, columns=[
            'id', 'evaluator_name', 'evaluator_class', 'target_grade', 
            'target_class', 'score1', 'score2', 'score3', 'total', 
            'note', 'created_at'
        ])
        
        # 时间处理
        def parse_datetime_robust(dt_str):
            if pd.isna(dt_str):
                return None
            dt_str = str(dt_str).strip()
            if '+' in dt_str:
                dt_str = dt_str.split('+')[0]
            if 'T' in dt_str:
                dt_str = dt_str.replace('T', ' ')
            try:
                return pd.to_datetime(dt_str)
            except:
                try:
                    date_part = dt_str.split()[0]
                    return pd.to_datetime(date_part)
                except:
                    return None
        
        df["created_at"] = df["created_at"].apply(parse_datetime_robust)
        df = df.dropna(subset=['created_at'])
        print(f"✅ 时间解析后: {len(df)}条")
        
        # 3. 检查是否有管理员记录
        admin_records = df[df['evaluator_name'].str.contains('admin|管理员', case=False, na=False)]
        print(f"🔍 管理员记录: {len(admin_records)}条")
        
        if len(admin_records) > 0:
            print("管理员记录示例:")
            print(admin_records[['evaluator_name', 'evaluator_class', 'target_grade', 'target_class', 'total']].head())
        
        # 4. 测试数据过滤（可选）
        print("\n🧪 测试数据过滤...")
        test_keywords = ['测试', 'test', 'Test', 'TEST']
        before_filter = len(df)
        
        for keyword in test_keywords:
            df = df[~df['evaluator_name'].str.contains(keyword, na=False)]
            df = df[~df['evaluator_class'].str.contains(keyword, na=False)]
        
        print(f"📊 排除测试数据后: {len(df)}条 (原{before_filter}条)")
        
        if df.empty:
            print("❌ 过滤后无数据")
            return False
        
        # 5. 计算评分周期
        print("\n📅 计算评分周期...")
        
        def get_biweekly_period(date):
            days_until_sunday = (6 - date.weekday()) % 7
            if days_until_sunday == 0 and date.weekday() != 6:
                days_until_sunday = 7
            current_sunday = date + timedelta(days=days_until_sunday)
            
            year_start = datetime(date.year, 1, 1).date()
            days_from_start = (current_sunday - year_start).days
            week_number = days_from_start // 7
            period_number = week_number // 2
            period_end_sunday = year_start + timedelta(days=(period_number * 14 + 13))
            
            while period_end_sunday.weekday() != 6:
                period_end_sunday += timedelta(days=1)
            
            return period_number, period_end_sunday
        
        df['date_only'] = df['created_at'].dt.date
        df['period_number'] = df['date_only'].apply(lambda x: get_biweekly_period(x)[0])
        df['period_end_date'] = df['date_only'].apply(lambda x: get_biweekly_period(x)[1])
        df['period_month'] = df['period_end_date'].apply(lambda x: x.strftime('%Y-%m'))
        
        print(f"周期分布:")
        print(df['period_month'].value_counts())
        
        # 6. 过滤月份数据
        month_df = df[df['period_month'] == month].copy()
        
        if month_df.empty:
            month_df = df.copy()
            print(f"⚠️ 按周期归属无数据，使用原始月份筛选")
        
        print(f"✅ 最终数据: {len(month_df)}条")
        
        # 7. 检查历史记录
        print("\n📚 检查历史记录...")
        history_sql = f"""
            SELECT COUNT(*) FROM scores_history h
            WHERE strftime('%Y-%m', h.original_created_at) = {placeholder}
        """
        cur.execute(history_sql, (month,))
        history_count = cur.fetchone()[0]
        print(f"历史记录数量: {history_count}条")
        
        # 8. 创建测试Excel
        print("\n📄 创建测试Excel...")
        filepath = os.path.join("exports", f"verified_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        
        with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
            # 简单的明细表
            detail_df = month_df.copy()
            detail_df['评分周期'] = detail_df['period_number'].apply(lambda x: f"第{x + 1}周期")
            detail_df = detail_df[['evaluator_name', 'evaluator_class', 'target_grade', 'target_class', 'total', 'score1', 'score2', 'score3', 'note', 'created_at', '评分周期']]
            detail_df.columns = ['评分者', '评分班级', '被查年级', '被查班级', '总分', '整洁分', '摆放分', '使用分', '备注', '评分时间', '评分周期']
            
            detail_df = detail_df.sort_values('评分时间')
            detail_df.to_excel(writer, sheet_name="验证数据", index=False)
        
        print(f"✅ 测试Excel创建成功: {filepath}")
        print(f"📊 包含数据: {len(detail_df)}条记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        put_conn(conn)

if __name__ == "__main__":
    result = verify_export_logic()
    print(f"\n🎯 验证结果: {'成功' if result else '失败'}")
