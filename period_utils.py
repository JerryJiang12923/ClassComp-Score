#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
周期计算工具模块
统一管理评分周期相关的计算逻辑
"""

from datetime import datetime, timedelta
import pytz
import os

# 周期计算常量
DAYS_IN_TWO_WEEKS = 14
PERIOD_BUFFER_DAYS = 13
SUNDAY_WEEKDAY = 6  # Python中星期日是6
DEFAULT_TIMEZONE = 'Asia/Shanghai'

def get_local_timezone():
    """获取本地时区，优先使用环境变量"""
    tz_name = os.getenv('TZ', DEFAULT_TIMEZONE)
    try:
        return pytz.timezone(tz_name)
    except:
        return pytz.timezone(DEFAULT_TIMEZONE)  # 回退到默认时区

def get_current_time():
    """获取当前本地时间（时区感知）"""
    local_tz = get_local_timezone()
    utc_now = datetime.now(pytz.UTC)
    return utc_now.astimezone(local_tz)



def get_current_semester_config(conn=None):
    """获取当前活跃的学期配置"""
    should_close_conn = conn is None
    if conn is None:
        from db import get_conn, put_conn
        conn = get_conn()
        should_close_conn = True
    
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM semester_config WHERE is_active = 1 LIMIT 1')
        semester = cur.fetchone()
        
        if semester:
            # 获取班级配置 - 使用数据库兼容的占位符
            import os
            db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
            placeholder = "?" if db_url.startswith("sqlite") else "%s"
            
            cur.execute(f'''
                SELECT grade_name, class_name
                FROM semester_classes 
                WHERE semester_id = {placeholder} AND is_active = 1
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
                    END,
                    class_name
            ''', (semester['id'],))
            classes = cur.fetchall()
            
            return {
                'semester': semester,
                'classes': classes
            }
        return None
    finally:
        if should_close_conn:
            from db import put_conn
            put_conn(conn)

def calculate_period_info(target_date=None, semester_config=None):
    """
    根据学期配置计算评分周期信息
    使用第一周期结束日期作为基准进行计算
    """
    if target_date is None:
        # 使用时区感知的当前时间
        current_time = get_current_time()
        target_date = current_time.date()
    elif isinstance(target_date, str):
        # 如果传入的是字符串，转换为date对象
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    
    if semester_config is None:
        config_data = get_current_semester_config()
        if not config_data:
            # 如果没有学期配置，使用默认逻辑
            year_start = datetime(target_date.year, 1, 1).date()
        else:
            semester = config_data['semester']
            first_period_end = datetime.strptime(semester['first_period_end_date'], '%Y-%m-%d').date()
            # 从第一周期结束日期推算开始日期（往前13天）
            year_start = first_period_end - timedelta(days=PERIOD_BUFFER_DAYS)
    else:
        first_period_end = datetime.strptime(semester_config['first_period_end_date'], '%Y-%m-%d').date()
        # 从第一周期结束日期推算开始日期（往前13天）
        year_start = first_period_end - timedelta(days=PERIOD_BUFFER_DAYS)
    
    # 找到该日期所在的周日（本周或下周）
    days_until_sunday = (6 - target_date.weekday()) % 7
    if days_until_sunday == 0 and target_date.weekday() != SUNDAY_WEEKDAY:
        days_until_sunday = 7
    current_sunday = target_date + timedelta(days=days_until_sunday)
    
    # 计算从周期开始的周数
    days_from_start = (current_sunday - year_start).days
    week_number = max(0, days_from_start // 7)
    
    # 两周为一个周期
    period_number = week_number // 2
    period_start = year_start + timedelta(days=(period_number * DAYS_IN_TWO_WEEKS))
    period_end = year_start + timedelta(days=(period_number * DAYS_IN_TWO_WEEKS + PERIOD_BUFFER_DAYS))
    
    # 确保周期结束日是周日
    while period_end.weekday() != SUNDAY_WEEKDAY:
        period_end += timedelta(days=1)
    
    return {
        'period_number': period_number,
        'period_start': period_start,
        'period_end': period_end,
        'year_start': year_start
    }

def get_biweekly_period_end(date, conn=None):
    """计算日期所属的两周周期结束日（兼容旧接口）"""
    period_info = calculate_period_info(target_date=date)
    return period_info['period_end']
