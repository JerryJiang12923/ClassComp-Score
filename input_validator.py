#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
输入验证和清理模块
防止SQL注入、XSS、目录遍历等攻击
"""

import re
import html
from security_constants import ALLOWED_GRADES, SCORE_VALIDATION, USER_ROLES

class InputValidator:
    """输入验证器"""
    
    @staticmethod
    def validate_grade(grade):
        """验证年级输入"""
        if not grade or not isinstance(grade, str):
            return False
        grade = grade.strip()
        return grade in ALLOWED_GRADES
    
    @staticmethod
    def validate_class_name(class_name):
        """验证班级名称"""
        if not class_name or not isinstance(class_name, str):
            return False
        class_name = class_name.strip()
        # 只允许中文、英文、数字和常见符号
        pattern = r'^[\u4e00-\u9fa5a-zA-Z0-9\-_\s]{1,50}$'
        return bool(re.match(pattern, class_name))
    
    @staticmethod
    def validate_username(username):
        """验证用户名"""
        if not username or not isinstance(username, str):
            return False
        username = username.strip()
        # 用户名只允许字母、数字、下划线，3-20位
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_score(score):
        """验证分数"""
        try:
            score_int = int(score)
            return SCORE_VALIDATION['MIN_SCORE'] <= score_int <= SCORE_VALIDATION['MAX_SCORE']
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_role(role):
        """验证用户角色"""
        return role in USER_ROLES.values()
    
    @staticmethod
    def sanitize_text(text, max_length=50):
        """清理文本输入，防止XSS"""
        if not text:
            return ""
        text = str(text).strip()
        # HTML转义
        text = html.escape(text)
        # 限制长度
        if len(text) > max_length:
            text = text[:max_length]
        return text
    
    @staticmethod
    def validate_date_format(date_str):
        """验证日期格式 YYYY-MM-DD"""
        if not date_str:
            return False
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(pattern, date_str))
    
    @staticmethod
    def validate_month_format(month_str):
        """验证月份格式 YYYY-MM"""
        if not month_str:
            return False
        pattern = r'^\d{4}-\d{2}$'
        return bool(re.match(pattern, month_str))

class SQLSafetyHelper:
    """SQL安全助手"""
    
    @staticmethod
    def build_grade_filter(teacher_grade, include_vce=False):
        """构建安全的年级过滤条件"""
        if not InputValidator.validate_grade(teacher_grade):
            return "", []
        
        if include_vce and teacher_grade in ['高一', '高二']:
            return " AND (target_grade LIKE ? OR target_grade LIKE ?)", [f'%{teacher_grade}%', f'%{teacher_grade}VCE%']
        else:
            return " AND target_grade LIKE ?", [f'%{teacher_grade}%']
    
    @staticmethod
    def build_in_clause(values):
        """构建安全的IN子句"""
        if not values:
            return "", []
        placeholders = ','.join(['?' for _ in values])
        return f" IN ({placeholders})", list(values)
    
    @staticmethod
    def escape_like_pattern(pattern):
        """转义LIKE模式中的特殊字符"""
        if not pattern:
            return ""
        # 转义 % 和 _ 字符
        escaped = pattern.replace('%', '\\%').replace('_', '\\_')
        return escaped

# 装饰器用于自动验证输入
def validate_input(**validators):
    """输入验证装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 在这里可以添加自动验证逻辑
            return func(*args, **kwargs)
        return wrapper
    return decorator
