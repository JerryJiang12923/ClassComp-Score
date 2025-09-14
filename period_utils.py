#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
周期计算工具模块
统一管理评分周期相关的计算逻辑
"""

from datetime import datetime, timedelta
import pytz
import os

# 导入班级排序工具
from class_sorting_utils import generate_class_sorting_sql

# 周期计算常量
DAYS_IN_TWO_WEEKS = 14
PERIOD_BUFFER_DAYS = 13
SUNDAY_WEEKDAY = 6  # Python中星期日是6
DEFAULT_TIMEZONE = 'Asia/Shanghai'

def get_local_timezone():
    """强制使用上海时区"""
    return pytz.timezone(DEFAULT_TIMEZONE)

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
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        placeholder = "?" if db_url.startswith("sqlite") else "%s"
        cur.execute(f'SELECT * FROM semester_config WHERE is_active = {placeholder} LIMIT 1', (1,))
        semester = cur.fetchone()
        
        if semester:
            # 获取班级配置 - 使用数据库兼容的占位符
            db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
            placeholder = "?" if db_url.startswith("sqlite") else "%s"
            
            class_sorting_sql = generate_class_sorting_sql("grade_name", "class_name")
            cur.execute(f'''
                SELECT grade_name, class_name
                FROM semester_classes 
                WHERE semester_id = {placeholder} AND is_active = 1
                ORDER BY {class_sorting_sql}
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

def calculate_period_info(target_date=None, semester_config=None, conn=None):
    """
    根据学期配置计算评分周期信息
    基于学期开始日期和第一周期结束日期进行计算
    """
    if target_date is None:
        # 使用时区感知的当前时间
        current_time = get_current_time()
        target_date = current_time.date()
    elif isinstance(target_date, str):
        # 如果传入的是字符串，转换为date对象
        target_date = get_local_timezone().localize(datetime.strptime(target_date, '%Y-%m-%d')).date()
    
    def _get_semester_info_from_config(config):
        """从学期配置获取开始日期和第一周期结束日期"""
        # 学期开始日期
        start_date_raw = config['start_date']
        if isinstance(start_date_raw, str):
            semester_start = get_local_timezone().localize(datetime.strptime(start_date_raw, '%Y-%m-%d')).date()
        else:
            semester_start = start_date_raw
        
        # 第一周期结束日期
        end_date_raw = config['first_period_end_date']
        if isinstance(end_date_raw, str):
            first_period_end = get_local_timezone().localize(datetime.strptime(end_date_raw, '%Y-%m-%d')).date()
        else:
            first_period_end = end_date_raw
        
        return semester_start, first_period_end

    if semester_config is None:
        config_data = get_current_semester_config(conn=conn)
        if not config_data:
            # 如果没有学期配置，使用默认逻辑
            year_start = datetime(target_date.year, 1, 1).date()
            # 默认第一周期14天
            first_period_end = year_start + timedelta(days=PERIOD_BUFFER_DAYS)
        else:
            year_start, first_period_end = _get_semester_info_from_config(config_data['semester'])
    else:
        year_start, first_period_end = _get_semester_info_from_config(semester_config)
    
    # 如果目标日期在第一周期内
    if year_start <= target_date <= first_period_end:
        return {
            'period_number': 0,
            'period_start': year_start,
            'period_end': first_period_end,
            'year_start': year_start
        }
    
    # 对于第一周期之后的日期，按14天一个周期计算
    days_after_first_period = (target_date - first_period_end).days
    
    if days_after_first_period <= 0:
        # 目标日期在第一周期内或之前
        return {
            'period_number': 0,
            'period_start': year_start,
            'period_end': first_period_end,
            'year_start': year_start
        }
    
    # 计算是第几个后续周期（从周期1开始）
    # days_after_first_period = 1 时应该在周期1的第一天
    additional_period_index = (days_after_first_period - 1) // DAYS_IN_TWO_WEEKS
    period_number = additional_period_index + 1
    
    # 计算该周期的开始和结束日期
    period_start = first_period_end + timedelta(days=1) + timedelta(days=additional_period_index * DAYS_IN_TWO_WEEKS)
    period_end = period_start + timedelta(days=PERIOD_BUFFER_DAYS)
    
    return {
        'period_number': period_number,
        'period_start': period_start,
        'period_end': period_end,
        'year_start': year_start
    }

def get_biweekly_period_end(date, conn=None):
    """计算日期所属的两周周期结束日（兼容旧接口）"""
    period_info = calculate_period_info(target_date=date, conn=conn)
    return period_info['period_end']
