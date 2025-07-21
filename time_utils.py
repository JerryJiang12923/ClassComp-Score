"""
时间处理工具模块
统一处理不同数据库的时间格式问题
"""

import pytz
import os
from datetime import datetime

def get_local_timezone():
    """强制使用上海时区"""
    return pytz.timezone('Asia/Shanghai')

def get_current_time():
    """获取当前本地时间（时区感知）"""
    local_tz = get_local_timezone()
    utc_now = datetime.now(pytz.UTC)
    return utc_now.astimezone(local_tz)

def parse_database_timestamp(timestamp_value):
    """
    统一解析数据库中的时间戳格式
    - PostgreSQL 返回带时区的 datetime 对象
    - SQLite 返回字符串
    """
    if timestamp_value is None:
        return None
    
    local_tz = get_local_timezone()
    
    if isinstance(timestamp_value, datetime):
        # 如果已经是 datetime 对象，确保其有时区信息
        if timestamp_value.tzinfo is None:
            return local_tz.localize(timestamp_value)
        return timestamp_value.astimezone(local_tz)
    
    if isinstance(timestamp_value, str):
        # SQLite 返回的是字符串，手动解析并赋予时区
        try:
            # 尝试解析不带时区信息的格式
            dt = datetime.strptime(timestamp_value, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                dt = datetime.strptime(timestamp_value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                print(f"无法解析SQLite时间字符串: {timestamp_value}")
                return get_current_time()
        
        return local_tz.localize(dt)
    
    print(f"未知的时间格式: {type(timestamp_value)}")
    return get_current_time()

def format_datetime_for_display(dt, format_string='%Y-%m-%d %H:%M:%S'):
    """格式化时间戳用于显示"""
    if dt is None:
        return ""
    
    if isinstance(dt, str):
        dt = parse_database_timestamp(dt)
    
    if isinstance(dt, datetime):
        return dt.strftime(format_string)
    
    return str(dt)

def format_datetime_for_database(dt=None):
    """格式化时间戳用于数据库存储"""
    if dt is None:
        dt = get_current_time()
    
    # 确保时区感知
    if isinstance(dt, datetime) and dt.tzinfo is None:
        local_tz = get_local_timezone()
        dt = local_tz.localize(dt)
    
    return dt
