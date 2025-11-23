"""
数据库模块包 - 数据库连接和管理
Database connection management for ClassComp Score system.
"""

from classcomp.database.connection import get_conn, put_conn

__all__ = ['get_conn', 'put_conn']