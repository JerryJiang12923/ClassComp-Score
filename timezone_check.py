#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
时区检查工具
用于验证应用的时区设置是否正确
"""

import os
import sys
from datetime import datetime
import pytz

def check_timezone_setup():
    """检查时区设置"""
    print("🕐 时区配置检查")
    print("=" * 50)
    
    # 1. 检查环境变量
    tz_env = os.getenv('TZ')
    print(f"📍 环境变量 TZ: {tz_env or '未设置'}")
    
    # 2. 系统时区
    import time
    system_tz = time.tzname
    print(f"🖥️  系统时区: {system_tz}")
    
    # 3. Python 默认时间
    local_time = datetime.now()
    utc_time = datetime.utcnow()
    print(f"🐍 Python 本地时间: {local_time}")
    print(f"🌍 Python UTC 时间: {utc_time}")
    
    # 4. 应用时区设置
    try:
        from models import get_current_time, get_local_timezone
        app_tz = get_local_timezone()
        app_time = get_current_time()
        print(f"📱 应用时区: {app_tz}")
        print(f"📱 应用当前时间: {app_time}")
        print(f"📱 应用时间 (ISO): {app_time.isoformat()}")
        
        # 5. 与期望时区比较
        expected_tz = pytz.timezone('Asia/Shanghai')
        expected_time = datetime.now(expected_tz)
        print(f"🎯 期望时区 (Asia/Shanghai): {expected_tz}")
        print(f"🎯 期望时间: {expected_time}")
        
        # 6. 时差检查
        time_diff = abs((app_time.replace(tzinfo=None) - expected_time.replace(tzinfo=None)).total_seconds())
        if time_diff <= 1:  # 允许1秒误差
            print("✅ 时区设置正确！")
            return True
        else:
            print(f"❌ 时区设置错误！时差: {time_diff} 秒")
            return False
            
    except ImportError as e:
        print(f"❌ 无法导入应用模块: {e}")
        return False
    except Exception as e:
        print(f"❌ 时区检查失败: {e}")
        return False

def simulate_scoring_time():
    """模拟评分时间场景"""
    print("\n📝 评分时间场景模拟")
    print("=" * 50)
    
    try:
        from models import get_current_time
        from period_utils import calculate_period_info
        
        # 模拟晚上10点提交评分
        current_time = get_current_time()
        print(f"当前时间: {current_time}")
        
        # 计算周期信息
        period_info = calculate_period_info()
        print(f"当前周期: 第{period_info['period_number'] + 1}周期")
        print(f"周期开始: {period_info['period_start']}")
        print(f"周期结束: {period_info['period_end']}")
        
        # 检查是否在正确的日期
        today = current_time.date()
        if period_info['period_start'] <= today <= period_info['period_end']:
            print("✅ 当前日期在正确的评分周期内")
        else:
            print("❌ 当前日期不在预期的评分周期内")
            
    except Exception as e:
        print(f"❌ 周期计算失败: {e}")

def test_database_timezone():
    """测试数据库时区"""
    print("\n💾 数据库时区测试")
    print("=" * 50)
    
    try:
        from db import get_conn, put_conn
        
        conn = get_conn()
        cur = conn.cursor()
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        
        if is_sqlite:
            # SQLite 时间函数测试
            cur.execute("SELECT datetime('now') as db_time")
            result = cur.fetchone()
            print(f"SQLite datetime('now'): {result['db_time'] if result else 'None'}")
            
            cur.execute("SELECT strftime('%s', 'now') as timestamp")
            result = cur.fetchone()
            if result:
                import datetime
                db_timestamp = datetime.datetime.fromtimestamp(int(result['timestamp']))
                print(f"SQLite Unix 时间戳: {db_timestamp}")
        else:
            # PostgreSQL 时间函数测试
            cur.execute("SELECT NOW() as db_time, CURRENT_TIMESTAMP as current_ts")
            result = cur.fetchone()
            if result:
                print(f"PostgreSQL NOW(): {result['db_time']}")
                print(f"PostgreSQL CURRENT_TIMESTAMP: {result['current_ts']}")
        
        put_conn(conn)
        
    except Exception as e:
        print(f"❌ 数据库时区测试失败: {e}")

if __name__ == "__main__":
    print("🚀 ClassComp Score 时区检查工具")
    print("=" * 60)
    
    success = check_timezone_setup()
    simulate_scoring_time()
    test_database_timezone()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 时区配置检查通过！")
        print("💡 建议：在部署到 Render 前，确保设置了 TZ=Asia/Shanghai 环境变量")
    else:
        print("❌ 时区配置有问题，需要修复！")
        print("💡 解决方案：")
        print("   1. 在 render.yaml 中添加 TZ=Asia/Shanghai 环境变量")
        print("   2. 确保应用代码使用时区感知的时间函数")
        print("   3. 在 Render 控制台中验证环境变量设置")
    
    sys.exit(0 if success else 1)
