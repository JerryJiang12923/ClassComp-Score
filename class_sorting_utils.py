#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
班级排序工具函数
提供通用的班级名称数字排序功能
"""

import re
import os

def get_class_number_sql(class_name_column):
    """
    返回适用于SQLite和PostgreSQL的班级数字提取SQL表达式
    
    Args:
        class_name_column (str): 班级名称列名，如 'class_name' 或 'sc.class_name'
    
    Returns:
        str: 用于提取班级数字的SQL表达式
    """
    
    db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
    is_sqlite = db_url.startswith("sqlite")
    
    if is_sqlite:
        # SQLite版本：使用字符串替换提取数字
        return f"""
        CASE 
            WHEN TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                {class_name_column}, '班', ''), '年级', ''), '中预', ''), '初一', ''), '初二', ''), 
                '初三', ''), '高一', ''), '高二', ''), '高三', ''), 'VCE', ''), '') != ''
            THEN CAST(TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                {class_name_column}, '班', ''), '年级', ''), '中预', ''), '初一', ''), '初二', ''), 
                '初三', ''), '高一', ''), '高二', ''), '高三', ''), 'VCE', ''), '') AS INTEGER)
            ELSE 0
        END"""
    else:
        # PostgreSQL版本：使用正则表达式
        return f"""
        CASE 
            WHEN {class_name_column} ~ '[0-9]+' THEN 
                CAST(REGEXP_REPLACE({class_name_column}, '[^0-9]', '', 'g') AS INTEGER)
            ELSE 0
        END"""

def get_grade_order_sql(grade_name_column):
    """
    返回年级排序的SQL表达式
    
    Args:
        grade_name_column (str): 年级名称列名，如 'grade_name' 或 'sc.grade_name'
    
    Returns:
        str: 年级排序的SQL表达式
    """
    return f"""
    CASE {grade_name_column} 
        WHEN '中预' THEN 1
        WHEN '初一' THEN 2
        WHEN '初二' THEN 3
        WHEN '初三' THEN 4
        WHEN '高一' THEN 5
        WHEN '高二' THEN 6
        WHEN '高三' THEN 7
        WHEN '高一VCE' THEN 8
        WHEN '高二VCE' THEN 9
        WHEN '高三VCE' THEN 10
        ELSE 99
    END"""

def generate_class_sorting_sql(grade_name_column, class_name_column):
    """
    生成完整的班级排序SQL子句
    
    Args:
        grade_name_column (str): 年级名称列名
        class_name_column (str): 班级名称列名
    
    Returns:
        str: 完整的排序SQL子句（不包含ORDER BY关键字）
    """
    grade_order = get_grade_order_sql(grade_name_column)
    class_number = get_class_number_sql(class_name_column)
    
    return f"{grade_order}, {class_number}, {class_name_column}"

def get_complete_class_order_sql(grade_column="grade_name", class_column="class_name"):
    """
    返回完整的班级排序SQL语句
    先按年级排序，再按班级数字排序，最后按班级名称排序
    
    Args:
        grade_column (str): 年级列名
        class_column (str): 班级列名
    
    Returns:
        str: 完整的ORDER BY子句
    """
    grade_order = get_grade_order_sql(grade_column)
    class_number = get_class_number_sql(class_column)
    
    return f"""
    ORDER BY 
        {grade_order},
        {class_number},
        {class_column}
    """

def extract_class_number(class_name):
    """
    Python函数：从班级名称中提取数字
    用于需要在Python中进行排序的场景
    
    Args:
        class_name (str): 班级名称，如 "中预10班"
        
    Returns:
        int: 提取的数字，如果没有数字则返回0
    """
    # 使用正则表达式提取数字
    match = re.search(r'(\d+)', class_name)
    if match:
        return int(match.group(1))
    return 0

def sort_classes_python(classes_list):
    """
    Python函数：对班级列表进行排序
    
    Args:
        classes_list (list): 班级字典列表，每个字典包含 grade_name 和 class_name
        
    Returns:
        list: 排序后的班级列表
    """
    grade_order = {
        '中预': 1, '初一': 2, '初二': 3, '初三': 4,
        '高一': 5, '高二': 6, '高三': 7,
        '高一VCE': 8, '高二VCE': 9, '高三VCE': 10
    }
    
    def sort_key(class_item):
        grade = class_item.get('grade_name', '')
        class_name = class_item.get('class_name', '')
        
        grade_num = grade_order.get(grade, 99)
        class_num = extract_class_number(class_name)
        
        return (grade_num, class_num, class_name)
    
    return sorted(classes_list, key=sort_key)

# 测试函数
if __name__ == '__main__':
    # 测试班级数字提取
    test_classes = ['中预1班', '中预2班', '中预9班', '中预10班', '高一VCE']
    
    print("测试班级数字提取:")
    for class_name in test_classes:
        number = extract_class_number(class_name)
        print(f"  {class_name} -> {number}")
    
    # 测试班级排序
    test_data = [
        {'grade_name': '中预', 'class_name': '中预10班'},
        {'grade_name': '中预', 'class_name': '中预1班'},
        {'grade_name': '初一', 'class_name': '初一2班'},
        {'grade_name': '中预', 'class_name': '中预9班'},
        {'grade_name': '初一', 'class_name': '初一10班'},
        {'grade_name': '高一VCE', 'class_name': '高一VCE'},
    ]
    
    print("\n测试班级排序:")
    print("排序前:")
    for item in test_data:
        print(f"  {item['grade_name']} - {item['class_name']}")
    
    sorted_data = sort_classes_python(test_data)
    print("排序后:")
    for item in sorted_data:
        print(f"  {item['grade_name']} - {item['class_name']}")
    
    print("\n生成的SQL ORDER BY 子句:")
    print(get_complete_class_order_sql())
