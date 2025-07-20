#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库连接管理器
确保连接正确关闭，防止连接泄露
"""

import sqlite3
import psycopg2
import os
from contextlib import contextmanager
from security_constants import DB_SECURITY

class DatabaseManager:
    """数据库连接管理器"""
    
    @staticmethod
    @contextmanager
    def get_connection():
        """安全的数据库连接上下文管理器"""
        conn = None
        try:
            db_url = os.getenv("DATABASE_URL", "sqlite:///classcomp.db")
            
            if db_url.startswith("postgresql"):
                conn = psycopg2.connect(
                    db_url,
                    connect_timeout=DB_SECURITY['CONNECTION_TIMEOUT']
                )
                conn.cursor().execute("SET statement_timeout = %s", (DB_SECURITY['QUERY_TIMEOUT'] * 1000,))
            else:
                # SQLite
                db_path = db_url.replace("sqlite:///", "")
                conn = sqlite3.connect(
                    db_path,
                    timeout=DB_SECURITY['CONNECTION_TIMEOUT']
                )
                conn.row_factory = sqlite3.Row
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def execute_safe_query(query, params=None, fetch_one=False, fetch_all=False):
        """执行安全的数据库查询"""
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
    
    @staticmethod
    def execute_transaction(operations):
        """执行事务操作"""
        with DatabaseManager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                for query, params in operations:
                    cursor.execute(query, params or [])
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise e
