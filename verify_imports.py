#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入验证脚本 - 验证重组后的项目结构
"""

import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """测试所有关键模块的导入"""
    errors = []
    successes = []
    
    # 测试数据库模块
    try:
        from classcomp.database import get_conn, put_conn
        successes.append("[OK] classcomp.database")
    except ImportError as e:
        errors.append(f"[FAIL] classcomp.database: {e}")
    
    # 测试模型模块
    try:
        from classcomp.models import User, Score, UserRealName
        successes.append("[OK] classcomp.models")
    except ImportError as e:
        errors.append(f"[FAIL] classcomp.models: {e}")
    
    # 测试表单模块
    try:
        from classcomp.forms import LoginForm, InfoCommitteeRegistrationForm, ScoreForm
        successes.append("[OK] classcomp.forms")
    except ImportError as e:
        errors.append(f"[FAIL] classcomp.forms: {e}")
    
    # 测试时间工具
    try:
        from classcomp.utils.time_utils import get_current_time, get_local_timezone
        successes.append("[OK] classcomp.utils.time_utils")
    except ImportError as e:
        errors.append(f"[FAIL] classcomp.utils.time_utils: {e}")
    
    # 测试周期工具
    try:
        from classcomp.utils.period_utils import get_current_semester_config, calculate_period_info
        successes.append("[OK] classcomp.utils.period_utils")
    except ImportError as e:
        errors.append(f"[FAIL] classcomp.utils.period_utils: {e}")
    
    # 测试班级排序工具
    try:
        from classcomp.utils.class_sorting_utils import generate_class_sorting_sql
        successes.append("[OK] classcomp.utils.class_sorting_utils")
    except ImportError as e:
        errors.append(f"[FAIL] classcomp.utils.class_sorting_utils: {e}")
    
    # 测试验证器
    try:
        from classcomp.utils.validators import InputValidator, SQLSafetyHelper
        successes.append("[OK] classcomp.utils.validators")
    except ImportError as e:
        errors.append(f"[FAIL] classcomp.utils.validators: {e}")
    
    # 测试中间件
    try:
        from classcomp.middleware import security_middleware
        successes.append("[OK] classcomp.middleware")
    except ImportError as e:
        errors.append(f"[FAIL] classcomp.middleware: {e}")
    
    # 测试常量
    try:
        from classcomp.constants import ALLOWED_GRADES, PERIOD_CONSTANTS
        successes.append("[OK] classcomp.constants")
    except ImportError as e:
        errors.append(f"[FAIL] classcomp.constants: {e}")
    
    # 打印结果
    print("\n" + "="*60)
    print("导入验证结果")
    print("="*60)
    
    if successes:
        print("\n成功的导入:")
        for success in successes:
            print(f"  {success}")
    
    if errors:
        print("\n失败的导入:")
        for error in errors:
            print(f"  {error}")
    
    print("\n" + "="*60)
    print(f"总计: {len(successes)} 成功, {len(errors)} 失败")
    print("="*60 + "\n")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)