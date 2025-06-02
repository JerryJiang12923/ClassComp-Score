# db.py
import os
from psycopg2 import pool, extras
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

# 创建连接池（1~5 连接满足大多数小项目）
conn_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    dsn=DB_URL,
    cursor_factory=extras.RealDictCursor,  # 查询结果按 dict 返回
)

def get_conn():
    """从池里取一个连接（记得用完再放回）"""
    return conn_pool.getconn()

def put_conn(conn):
    conn_pool.putconn(conn)