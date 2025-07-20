"""
时间处理工具模块
统一处理不同数据库的时间格式问题
"""

import pytz
import os
from datetime import datetime

def get_local_timezone():
    """获取本地时区，优先使用环境变量"""
    tz_name = os.getenv('TZ', 'Asia/Shanghai')
    try:
        return pytz.timezone(tz_name)
    except:
        return pytz.timezone('Asia/Shanghai')  # 回退到上海时区

def get_current_time():
    """获取当前本地时间（时区感知）"""
    local_tz = get_local_timezone()
    utc_now = datetime.now(pytz.UTC)
    return utc_now.astimezone(local_tz)

def parse_database_timestamp(timestamp_value):
    """
    统一解析数据库中的时间戳格式
    支持多种格式：
    - SQLite 字符串格式
    - PostgreSQL 带时区的时间戳
    - 原始 datetime 对象
    """
    if timestamp_value is None:
        return None
    
    local_tz = get_local_timezone()
    
    try:
        # 如果已经是 datetime 对象
        if isinstance(timestamp_value, datetime):
            if timestamp_value.tzinfo is None:
                # 如果没有时区信息，添加本地时区
                return local_tz.localize(timestamp_value)
            else:
                # 转换到本地时区
                return timestamp_value.astimezone(local_tz)
        
        # 如果是字符串，尝试各种格式解析
        if isinstance(timestamp_value, str):
            # 处理 ISO 格式，带 Z 后缀 (UTC)
            if timestamp_value.endswith('Z'):
                dt = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                return dt.astimezone(local_tz)
            
            # 处理带时区信息的字符串
            elif '+' in timestamp_value or timestamp_value.endswith('00'):
                try:
                    dt = datetime.fromisoformat(timestamp_value)
                    return dt.astimezone(local_tz)
                except ValueError:
                    pass
            
            # 处理简单的 datetime 字符串（假设为本地时间）
            try:
                # 尝试各种可能的格式
                formats = [
                    '%Y-%m-%d %H:%M:%S.%f',  # 带微秒
                    '%Y-%m-%d %H:%M:%S',     # 标准格式
                    '%Y-%m-%d %H:%M',        # 不带秒
                    '%Y/%m/%d %H:%M:%S',     # 斜杠分隔
                ]
                
                for fmt in formats:
                    try:
                        dt = datetime.strptime(timestamp_value, fmt)
                        return local_tz.localize(dt)
                    except ValueError:
                        continue
                
                # 如果以上都失败，尝试 fromisoformat
                dt = datetime.fromisoformat(timestamp_value)
                if dt.tzinfo is None:
                    return local_tz.localize(dt)
                else:
                    return dt.astimezone(local_tz)
                    
            except ValueError:
                pass
    
    except Exception as e:
        print(f"时间解析错误: {timestamp_value}, 错误: {e}")
    
    # 如果所有解析都失败，返回当前时间
    print(f"无法解析时间格式: {timestamp_value}, 使用当前时间")
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
