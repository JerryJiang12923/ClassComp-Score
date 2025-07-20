#!/usr/bin/env python3
"""
跨平台 WSGI 服务器启动脚本
- 自动检查和初始化数据库
- Windows: 使用 Waitress
- Linux/Mac: 使用 Gunicorn
"""
import os
import sys
import platform

def ensure_database_initialized():
    """确保数据库已初始化"""
    print("🔍 检查数据库状态...")
    
    try:
        from db import get_conn, put_conn
        conn = get_conn()
        cur = conn.cursor()
        
        # 检测数据库类型
        db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
        is_sqlite = db_url.startswith("sqlite")
        
        if is_sqlite:
            # SQLite 检查表存在性
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            users_exists = cur.fetchone()
            
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='semester_config'")
            semester_exists = cur.fetchone()
        else:
            # PostgreSQL 检查表存在性
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name='users'")
            users_exists = cur.fetchone()
            
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name='semester_config'")
            semester_exists = cur.fetchone()
        
        put_conn(conn)
        
        # 如果关键表不存在，执行完整初始化
        if not users_exists or not semester_exists:
            print("🔄 检测到数据库不完整，执行初始化...")
            print(f"  - users表存在: {users_exists is not None}")
            print(f"  - semester_config表存在: {semester_exists is not None}")
            
            from init_db import init_database
            init_database()
            print("✅ 数据库初始化完成")
        else:
            print("✅ 数据库表完整，连接正常")
            
    except Exception as e:
        print(f"⚠️ 数据库检查失败: {e}")
        print("🔄 尝试完整初始化...")
        try:
            from init_db import init_database
            init_database()
            print("✅ 数据库初始化完成")
        except Exception as init_e:
            print(f"❌ 数据库初始化失败: {init_e}")
            print("💡 请检查数据库连接和权限")
            sys.exit(1)

def start_server():
    """启动适合当前平台的 WSGI 服务器"""
    
    # 首先确保数据库已初始化
    ensure_database_initialized()
    
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"
    
    # 检查是否为生产环境
    is_production = os.environ.get("FLASK_ENV") == "production"
    
    if platform.system() == "Windows":
        # Windows 使用 Waitress
        print(f"🚀 Windows 环境检测到，使用 Waitress 启动服务器")
        print(f"📍 监听地址: {host}:{port}")
        
        try:
            from waitress import serve
            from wsgi import application
            
            # Waitress 配置
            serve(
                application,
                host=host,
                port=port,
                threads=4,  # 线程数
                connection_limit=1000,
                cleanup_interval=30,
                channel_timeout=120
            )
        except ImportError:
            print("❌ Waitress 未安装，请运行: pip install waitress")
            sys.exit(1)
            
    else:
        # Linux/Mac 使用 Gunicorn
        print(f"🚀 Unix 环境检测到，使用 Gunicorn 启动服务器")
        print(f"📍 监听地址: {host}:{port}")
        
        try:
            # 使用 exec 启动 Gunicorn
            gunicorn_cmd = [
                "gunicorn",
                "--config", "gunicorn.conf.py",
                "wsgi:application"
            ]
            
            os.execvp("gunicorn", gunicorn_cmd)
        except FileNotFoundError:
            print("❌ Gunicorn 未安装，请运行: pip install gunicorn")
            sys.exit(1)

if __name__ == "__main__":
    start_server()
