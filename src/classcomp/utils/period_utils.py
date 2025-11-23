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
from classcomp.utils.class_sorting_utils import generate_class_sorting_sql

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
        from classcomp.database import get_conn, put_conn
        conn = get_conn()
        should_close_conn = True
    
    try:
        cur = conn.cursor()
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        placeholder = "?" if db_url.startswith("sqlite") else "%s"
        cur.execute(f'SELECT * FROM semester_config WHERE is_active = {placeholder} LIMIT 1', (1,))
        semester_row = cur.fetchone()
        
        if semester_row:
            # 将Row对象转换为字典
            semester = dict(semester_row)
            
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
            classes_rows = cur.fetchall()
            
            # 将班级Row对象也转换为字典列表
            classes = [dict(row) for row in classes_rows]
            
            return {
                'semester': semester,
                'classes': classes
            }
        return None
    finally:
        if should_close_conn:
            from classcomp.database import put_conn
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


# ==================== V2: 动态周期支持 ====================

def get_period_from_metadata(target_date, semester_id, conn):
    """
    从 period_metadata 表查询指定日期所属的周期
    
    参数:
        target_date: 目标日期（date对象或字符串）
        semester_id: 学期ID
        conn: 数据库连接
    
    返回:
        周期信息字典，如果未找到则返回 None
        {
            'period_number': int,
            'period_type': 'weekly' | 'biweekly',
            'period_start': date,
            'period_end': date,
            'semester_id': int
        }
    """
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    
    cur = conn.cursor()
    db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
    is_sqlite = db_url.startswith("sqlite")
    placeholder = "?" if is_sqlite else "%s"
    
    # 查询包含该日期的周期
    if is_sqlite:
        cur.execute(f"""
            SELECT period_number, period_type, start_date, end_date
            FROM period_metadata
            WHERE semester_id = {placeholder}
              AND {placeholder} BETWEEN start_date AND end_date
              AND is_active = 1
            LIMIT 1
        """, (semester_id, target_date.strftime('%Y-%m-%d')))
    else:
        cur.execute(f"""
            SELECT period_number, period_type, start_date, end_date
            FROM period_metadata
            WHERE semester_id = {placeholder}
              AND {placeholder} BETWEEN start_date AND end_date
              AND is_active = 1
            LIMIT 1
        """, (semester_id, target_date))
    
    row = cur.fetchone()
    
    if row:
        # 转换日期格式
        start_date = row['start_date'] if hasattr(row, 'keys') else row[2]
        end_date = row['end_date'] if hasattr(row, 'keys') else row[3]
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        return {
            'period_number': row['period_number'] if hasattr(row, 'keys') else row[0],
            'period_type': row['period_type'] if hasattr(row, 'keys') else row[1],
            'period_start': start_date,
            'period_end': end_date,
            'semester_id': semester_id
        }
    
    return None


def create_next_period(semester_id, semester_config, conn):
    """
    创建下一个周期的元数据记录
    
    参数:
        semester_id: 学期ID
        semester_config: 学期配置字典
        conn: 数据库连接
    
    返回:
        新创建的周期信息字典
    """
    cur = conn.cursor()
    db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
    is_sqlite = db_url.startswith("sqlite")
    placeholder = "?" if is_sqlite else "%s"
    
    # 获取当前周期类型
    try:
        current_period_type = semester_config['current_period_type']
    except (KeyError, TypeError):
        current_period_type = 'biweekly'
    
    # 确定周期长度
    period_days = 7 if current_period_type == 'weekly' else 14
    
    # 获取最后一个周期
    cur.execute(f"""
        SELECT period_number, end_date
        FROM period_metadata
        WHERE semester_id = {placeholder}
        ORDER BY period_number DESC
        LIMIT 1
    """, (semester_id,))
    
    last_period = cur.fetchone()
    
    if last_period:
        # 有历史周期，基于最后一个周期计算
        last_period_number = last_period['period_number'] if hasattr(last_period, 'keys') else last_period[0]
        last_end_date = last_period['end_date'] if hasattr(last_period, 'keys') else last_period[1]
        
        if isinstance(last_end_date, str):
            last_end_date = datetime.strptime(last_end_date, '%Y-%m-%d').date()
        
        new_period_number = last_period_number + 1
        new_start_date = last_end_date + timedelta(days=1)
    else:
        # 没有历史周期，这是第一个周期（周期0）
        new_period_number = 0
        
        # 从学期配置获取开始日期
        start_date_raw = semester_config['start_date']
        if isinstance(start_date_raw, str):
            new_start_date = datetime.strptime(start_date_raw, '%Y-%m-%d').date()
        else:
            new_start_date = start_date_raw
    
    # 计算结束日期
    new_end_date = new_start_date + timedelta(days=period_days - 1)
    
    # 插入新周期
    if is_sqlite:
        cur.execute("""
            INSERT INTO period_metadata
            (semester_id, period_number, period_type, start_date, end_date, created_by)
            VALUES (?, ?, ?, ?, ?, 'system')
        """, (semester_id, new_period_number, current_period_type,
              new_start_date.strftime('%Y-%m-%d'), new_end_date.strftime('%Y-%m-%d')))
    else:
        cur.execute("""
            INSERT INTO period_metadata
            (semester_id, period_number, period_type, start_date, end_date, created_by)
            VALUES (%s, %s, %s, %s, %s, 'system')
        """, (semester_id, new_period_number, current_period_type,
              new_start_date, new_end_date))
    
    conn.commit()
    
    return {
        'period_number': new_period_number,
        'period_type': current_period_type,
        'period_start': new_start_date,
        'period_end': new_end_date,
        'semester_id': semester_id
    }


def calculate_period_info_v2(target_date=None, semester_config=None, conn=None):
    """
    V2版本：基于 period_metadata 表计算周期信息，支持动态周期类型
    
    优先级：
    1. 如果 period_metadata 表中存在该日期的记录，直接返回
    2. 如果不存在，动态创建新的周期记录
    
    参数:
        target_date: 目标日期（默认为当前日期）
        semester_config: 学期配置字典（可选）
        conn: 数据库连接（可选）
    
    返回:
        {
            'period_number': int,
            'period_type': 'weekly' | 'biweekly',
            'period_start': date,
            'period_end': date,
            'semester_id': int
        }
    """
    should_close_conn = conn is None
    if conn is None:
        from classcomp.database import get_conn, put_conn
        conn = get_conn()
    
    try:
        # 处理目标日期
        if target_date is None:
            current_time = get_current_time()
            target_date = current_time.date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # 获取学期配置
        if semester_config is None:
            config_data = get_current_semester_config(conn=conn)
            if not config_data:
                # 回退到旧版逻辑
                return calculate_period_info(target_date=target_date, conn=conn)
            semester_config = config_data['semester']
        
        semester_id = semester_config['id']
        
        # 1. 尝试从 period_metadata 表查询
        period_info = get_period_from_metadata(target_date, semester_id, conn)
        
        if period_info:
            return period_info
        
        # 2. 未找到，需要创建新周期
        # 首先检查是否需要创建多个周期来填补空缺
        cur = conn.cursor()
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        # 获取最后一个周期
        cur.execute(f"""
            SELECT period_number, end_date
            FROM period_metadata
            WHERE semester_id = {placeholder}
            ORDER BY period_number DESC
            LIMIT 1
        """, (semester_id,))
        
        last_period = cur.fetchone()
        
        if last_period:
            last_end_date = last_period['end_date'] if hasattr(last_period, 'keys') else last_period[1]
            if isinstance(last_end_date, str):
                last_end_date = datetime.strptime(last_end_date, '%Y-%m-%d').date()
            
            # 如果目标日期在最后周期结束日期之前，说明数据有问题
            if target_date <= last_end_date:
                # 这种情况不应该发生，因为前面应该查询到了
                # 回退到旧版逻辑
                return calculate_period_info(target_date=target_date, semester_config=semester_config, conn=conn)
        
        # 创建周期直到覆盖目标日期
        max_iterations = 100  # 防止无限循环
        iteration = 0
        
        while iteration < max_iterations:
            new_period = create_next_period(semester_id, semester_config, conn)
            
            # 检查新周期是否覆盖目标日期
            if new_period['period_start'] <= target_date <= new_period['period_end']:
                return new_period
            
            # 如果新周期的结束日期还在目标日期之前，继续创建
            if new_period['period_end'] < target_date:
                iteration += 1
                continue
            else:
                # 新周期超过了目标日期，说明目标日期在间隙中（不应该发生）
                break
        
        # 如果循环结束还没找到，回退到旧版逻辑
        print(f"警告：无法为日期 {target_date} 创建周期，回退到旧版计算")
        return calculate_period_info(target_date=target_date, semester_config=semester_config, conn=conn)
    
    finally:
        if should_close_conn:
            from classcomp.database import put_conn
            put_conn(conn)


def change_period_type(semester_id, new_type, effective_from_date, changed_by, reason=None, conn=None):
    """
    变更周期类型配置
    
    参数:
        semester_id: 学期ID
        new_type: 新的周期类型 ('weekly' 或 'biweekly')
        effective_from_date: 生效日期
        changed_by: 变更操作者
        reason: 变更原因（可选）
        conn: 数据库连接（可选）
    
    返回:
        (success: bool, message: str, effective_period_number: int)
    """
    should_close_conn = conn is None
    if conn is None:
        from classcomp.database import get_conn, put_conn
        conn = get_conn()
    
    try:
        cur = conn.cursor()
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        # 验证周期类型
        if new_type not in ['weekly', 'biweekly']:
            return False, "无效的周期类型，必须是 'weekly' 或 'biweekly'", None
        
        # 转换日期
        if isinstance(effective_from_date, str):
            effective_from_date = datetime.strptime(effective_from_date, '%Y-%m-%d').date()
        
        # 验证生效日期必须在未来
        current_date = get_current_time().date()
        if effective_from_date <= current_date:
            return False, "生效日期必须是未来日期", None
        
        # 获取学期配置
        cur.execute(f"""
            SELECT id, semester_name, current_period_type
            FROM semester_config
            WHERE id = {placeholder}
        """, (semester_id,))
        
        semester = cur.fetchone()
        if not semester:
            return False, "学期不存在", None
        
        current_type = semester['current_period_type'] if hasattr(semester, 'keys') else semester[2]
        
        # 检查是否真的需要变更
        if current_type == new_type:
            return False, f"当前周期类型已经是 {new_type}，无需变更", None
        
        # 查找生效日期所属的周期
        period_info = get_period_from_metadata(effective_from_date, semester_id, conn)
        
        if period_info:
            effective_period_number = period_info['period_number']
        else:
            # 如果生效日期还没有周期，计算它将属于哪个周期号
            cur.execute(f"""
                SELECT MAX(period_number) as max_period
                FROM period_metadata
                WHERE semester_id = {placeholder}
            """, (semester_id,))
            
            result = cur.fetchone()
            max_period = result['max_period'] if hasattr(result, 'keys') else result[0]
            effective_period_number = (max_period + 1) if max_period is not None else 0
        
        # 更新 semester_config 表
        cur.execute(f"""
            UPDATE semester_config
            SET current_period_type = {placeholder}
            WHERE id = {placeholder}
        """, (new_type, semester_id))
        
        # 记录变更历史
        if is_sqlite:
            cur.execute("""
                INSERT INTO period_config_history
                (semester_id, config_type, effective_from_period, effective_from_date, changed_by, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (semester_id, new_type, effective_period_number,
                  effective_from_date.strftime('%Y-%m-%d'), changed_by, reason))
        else:
            cur.execute("""
                INSERT INTO period_config_history
                (semester_id, config_type, effective_from_period, effective_from_date, changed_by, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (semester_id, new_type, effective_period_number,
                  effective_from_date, changed_by, reason))
        
        conn.commit()
        
        type_label = '单周 (7天)' if new_type == 'weekly' else '双周 (14天)'
        return True, f"周期类型已变更为 {type_label}，将从第 {effective_period_number + 1} 周期（{effective_from_date}）开始生效", effective_period_number
    
    except Exception as e:
        conn.rollback()
        return False, f"变更失败: {str(e)}", None
    finally:
        if should_close_conn:
            from classcomp.database import put_conn
            put_conn(conn)
