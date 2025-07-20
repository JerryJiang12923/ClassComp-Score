#!/usr/bin/env python3
"""
启动前检查脚本
确保所有必要的环境变量和依赖都已正确配置
"""

import os
import sys
from datetime import datetime

def check_environment():
    """检查环境变量"""
    print("🔍 检查环境变量...")
    
    # 检查数据库 URL（有默认值）
    db_url = os.getenv('DATABASE_URL', 'sqlite:///classcomp.db')
    if db_url.startswith('postgresql://'):
        print(f"✅ DATABASE_URL: PostgreSQL (生产环境)")
    elif db_url.startswith('sqlite://'):
        print(f"✅ DATABASE_URL: SQLite (开发环境)")
    else:
        print(f"❌ DATABASE_URL 格式不正确: {db_url}")
        return False
    
    # 检查密钥（有默认值，但生产环境应该设置）
    secret_key = os.getenv('SECRET_KEY')
    if secret_key:
        if secret_key == 'your-secret-key-change-this':
            print(f"⚠️ SECRET_KEY: 使用默认值（请在生产环境中更改）")
        else:
            print(f"✅ SECRET_KEY: 已设置")
    else:
        print(f"⚠️ SECRET_KEY: 未设置，将使用默认值")
    
    # 检查 Flask 环境
    flask_env = os.getenv('FLASK_ENV', 'development')
    print(f"✅ FLASK_ENV: {flask_env}")
    
    # 生产环境特殊检查
    if flask_env == 'production':
        if not secret_key or secret_key == 'your-secret-key-change-this':
            print("❌ 生产环境必须设置安全的 SECRET_KEY")
            return False
        if not db_url.startswith('postgresql://'):
            print("⚠️ 生产环境推荐使用 PostgreSQL 数据库")
    
    return True

def check_database_connection():
    """检查数据库连接和表结构"""
    print("🔍 检查数据库连接和表结构...")
    
    try:
        from db import get_conn, put_conn
            
        conn = get_conn()
        cur = conn.cursor()
        
        # 检查数据库连接
        cur.execute('SELECT 1')
        print("✅ 数据库连接正常")
        
        # 检查基本表是否存在
        basic_tables = ['users', 'scores', 'scores_history']
        missing_tables = []
        
        db_url = os.getenv('DATABASE_URL', 'sqlite:///classcomp.db')
        is_sqlite = db_url.startswith('sqlite')
        
        for table_name in basic_tables:
            if is_sqlite:
                # SQLite 检查表存在性
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                table_exists = cur.fetchone()
            else:
                # PostgreSQL 检查表存在性
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name=%s", (table_name,))
                table_exists = cur.fetchone()
            
            if table_exists:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM {table_name}')
                    result = cur.fetchone()
                    count = result['count'] if hasattr(result, 'keys') else result[0]
                    print(f"✅ {table_name} 表存在 ({count} 条记录)")
                except Exception as e:
                    print(f"✅ {table_name} 表存在 (查询记录数失败: {e})")
            else:
                missing_tables.append(table_name)
                print(f"❌ {table_name} 表不存在")
        
        # 检查semester配置表
        semester_tables = ['semester_config', 'semester_classes']
        missing_semester_tables = []
        
        for table_name in semester_tables:
            if is_sqlite:
                # SQLite 检查表存在性
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                table_exists = cur.fetchone()
            else:
                # PostgreSQL 检查表存在性
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name=%s", (table_name,))
                table_exists = cur.fetchone()
            
            if table_exists:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM {table_name}')
                    result = cur.fetchone()
                    count = result['count'] if hasattr(result, 'keys') else result[0]
                    print(f"✅ {table_name} 表存在 ({count} 条记录)")
                except Exception as e:
                    print(f"✅ {table_name} 表存在 (查询记录数失败: {e})")
            else:
                missing_semester_tables.append(table_name)
                print(f"❌ {table_name} 表不存在")
        
        put_conn(conn)
        
        # 如果有缺失的表，尝试初始化数据库
        if missing_tables or missing_semester_tables:
            print("🔧 检测到缺失的表，尝试初始化数据库...")
            try:
                from init_db import init_database
                init_database()
                print("✅ 数据库初始化完成")
            except Exception as init_error:
                print(f"❌ 数据库初始化失败: {init_error}")
                return False
        else:
            # 即使表存在，也要确保管理员密码是最新的
            print("🔧 检查管理员账户密码...")
            try:
                from reset_admin_password import reset_admin_password
                reset_admin_password()
            except Exception as admin_error:
                print(f"⚠️ 管理员密码检查失败: {admin_error}")
                # 不返回 False，因为这不是致命错误

        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def check_dependencies():
    """检查关键依赖"""
    print("🔍 检查关键依赖...")
    
    required_modules = [
        'flask', 'flask_cors', 'flask_login', 'pandas', 
        'psycopg2', 'gunicorn', 'xlsxwriter'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module.replace('-', '_'))
            print(f"✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module}")
    
    if missing_modules:
        print(f"❌ 缺少依赖包: {', '.join(missing_modules)}")
        return False
    
    return True

def main():
    """主检查函数"""
    print(f"🚀 开始启动检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    checks = [
        ("环境变量", check_environment),
        ("依赖包", check_dependencies),
        ("数据库连接", check_database_connection),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} 检查出错: {e}")
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 所有检查通过，准备启动应用！")
        return 0
    else:
        print("💥 检查失败，请修复上述问题后重试")
        return 1

if __name__ == "__main__":
    sys.exit(main())
