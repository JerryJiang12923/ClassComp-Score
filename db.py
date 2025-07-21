# db.py
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_URL = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")  # 默认使用 SQLite

# 根据URL类型选择数据库
if DB_URL.startswith('sqlite'):
    # SQLite模式 - 开发环境
    import re
    db_filename = re.search(r'sqlite:///(.+)', DB_URL).group(1)
    # 如果是相对路径，则相对于脚本目录
    if not os.path.isabs(db_filename):
        db_path = os.path.join(BASE_DIR, db_filename)
    else:
        db_path = db_filename
    
    def get_conn():
        """获取SQLite连接"""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果支持dict-like访问
        return conn
    
    def put_conn(conn):
        """关闭SQLite连接"""
        conn.close()

else:
    # PostgreSQL模式 - 生产环境
    try:
        from psycopg2 import pool, extras
        
        conn_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=DB_URL,
            cursor_factory=extras.RealDictCursor,
        )
        
        def get_conn():
            """从池里取一个连接（记得用完再放回）"""
            conn = conn_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SET timezone = 'Asia/Shanghai'")
            return conn
        
        def put_conn(conn):
            conn_pool.putconn(conn)
    except ImportError:
        raise ImportError("PostgreSQL模式需要psycopg2-binary包")