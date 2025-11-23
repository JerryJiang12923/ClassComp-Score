"""
评分工具模块 - 包含加权评分计算逻辑
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src'))

from classcomp.database import get_conn, put_conn


def get_active_weight_config(conn=None):
    """获取当前活跃的权重配置"""
    should_close = False
    if conn is None:
        conn = get_conn()
        should_close = True
    
    try:
        cur = conn.cursor()
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        placeholder = "?" if db_url.startswith("sqlite") else "%s"
        
        cur.execute(f"""
            SELECT new_media_weight, info_commissioner_weight
            FROM score_weight_config
            WHERE is_active = {placeholder}
            LIMIT 1
        """, (True,))
        
        config = cur.fetchone()
        if config:
            return {
                'new_media_weight': float(config['new_media_weight']),
                'info_commissioner_weight': float(config['info_commissioner_weight'])
            }
        
        # 返回默认权重
        return {
            'new_media_weight': 1.5,
            'info_commissioner_weight': 1.0
        }
    finally:
        if should_close:
            put_conn(conn)


def calculate_weighted_scores(scores_data, conn=None):
    """
    计算加权后的班级平均分
    
    参数:
        scores_data: 评分数据列表，每条记录包含 total 和 source_type
        conn: 数据库连接（可选）
    
    返回:
        加权平均分
    """
    if not scores_data:
        return 0.0
    
    weights = get_active_weight_config(conn)
    
    total_weighted_score = 0.0
    total_weight = 0.0
    
    for score in scores_data:
        score_value = float(score.get('total', 0))
        source_type = score.get('source_type', 'info_commissioner')
        
        if source_type == 'new_media_officer':
            weight = weights['new_media_weight']
        else:
            weight = weights['info_commissioner_weight']
        
        total_weighted_score += score_value * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return round(total_weighted_score / total_weight, 2)


def get_class_weighted_average(target_grade, target_class, period_start, period_end, conn=None):
    """
    获取指定班级在指定周期内的加权平均分
    
    参数:
        target_grade: 目标年级
        target_class: 目标班级
        period_start: 周期开始日期
        period_end: 周期结束日期
        conn: 数据库连接（可选）
    
    返回:
        加权平均分
    """
    should_close = False
    if conn is None:
        conn = get_conn()
        should_close = True
    
    try:
        cur = conn.cursor()
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        if is_sqlite:
            date_func = "DATE(created_at)"
        else:
            date_func = "DATE(created_at AT TIME ZONE 'Asia/Shanghai')"
        
        cur.execute(f"""
            SELECT total, source_type
            FROM scores
            WHERE target_grade = {placeholder}
              AND target_class = {placeholder}
              AND {date_func} >= {placeholder}
              AND {date_func} <= {placeholder}
        """, (target_grade, target_class, period_start.strftime('%Y-%m-%d'), period_end.strftime('%Y-%m-%d')))
        
        scores = cur.fetchall()
        
        if not scores:
            return 0.0
        
        # 转换为字典列表
        scores_data = [{'total': s['total'], 'source_type': s.get('source_type', 'info_commissioner')} for s in scores]
        
        return calculate_weighted_scores(scores_data, conn)
    finally:
        if should_close:
            put_conn(conn)


def get_all_classes_weighted_average(period_start, period_end, conn=None):
    """
    获取所有班级在指定周期内的加权平均分
    
    参数:
        period_start: 周期开始日期
        period_end: 周期结束日期
        conn: 数据库连接（可选）
    
    返回:
        字典，键为 (target_grade, target_class)，值为加权平均分
    """
    should_close = False
    if conn is None:
        conn = get_conn()
        should_close = True
    
    try:
        cur = conn.cursor()
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        placeholder = "?" if is_sqlite else "%s"
        
        if is_sqlite:
            date_func = "DATE(created_at)"
        else:
            date_func = "DATE(created_at AT TIME ZONE 'Asia/Shanghai')"
        
        cur.execute(f"""
            SELECT target_grade, target_class, total, source_type
            FROM scores
            WHERE {date_func} >= {placeholder}
              AND {date_func} <= {placeholder}
            ORDER BY target_grade, target_class
        """, (period_start.strftime('%Y-%m-%d'), period_end.strftime('%Y-%m-%d')))
        
        all_scores = cur.fetchall()
        
        # 按班级分组
        class_scores = {}
        for score in all_scores:
            key = (score['target_grade'], score['target_class'])
            if key not in class_scores:
                class_scores[key] = []
            class_scores[key].append({
                'total': score['total'],
                'source_type': score.get('source_type', 'info_commissioner')
            })
        
        # 计算每个班级的加权平均分
        result = {}
        for key, scores in class_scores.items():
            result[key] = calculate_weighted_scores(scores, conn)
        
        return result
    finally:
        if should_close:
            put_conn(conn)