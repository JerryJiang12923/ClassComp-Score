#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全常量配置
"""

# 周期计算常量
PERIOD_CONSTANTS = {
    'DAYS_IN_PERIOD': 14,  # 两周一个周期
    'GRACE_DAYS': 1,       # 宽限天数
    'SUNDAY_WEEKDAY': 6,   # 星期日的weekday值
    'MAX_LOOP_ITERATIONS': 7,  # 防止无限循环的最大迭代次数
}

# 年级白名单
ALLOWED_GRADES = [
    '中预', '初一', '初二', '高一', '高二', '高一VCE', '高二VCE'
]

# 用户角色常量
USER_ROLES = {
    'ADMIN': 'admin',
    'TEACHER': 'teacher', 
    'STUDENT': 'student'
}

# 评分范围验证
SCORE_VALIDATION = {
    'MIN_SCORE': 0,
    'MAX_SCORE': 10,
    'SCORE_COMPONENTS': ['score1', 'score2', 'score3']
}

# 数据库安全配置
DB_SECURITY = {
    'MAX_CONNECTIONS': 100,
    'CONNECTION_TIMEOUT': 30,
    'QUERY_TIMEOUT': 60
}

# 文件上传安全
FILE_SECURITY = {
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'ALLOWED_EXTENSIONS': ['.xlsx', '.xls', '.db', '.sql'],
    'UPLOAD_FOLDER': 'exports'
}

# 会话安全
SESSION_SECURITY = {
    'SESSION_TIMEOUT': 3600,  # 1小时
    'MAX_LOGIN_ATTEMPTS': 10,  # 增加到10次（开发友好）
    'LOCKOUT_DURATION': 300    # 减少到5分钟（开发友好）
}
