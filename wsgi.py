#!/usr/bin/env python3
"""
WSGI 入口文件
用于 Gunicorn 等 WSGI 服务器
"""
import os
from app import app

# 导出 application 供 WSGI 服务器使用
application = app

if __name__ == "__main__":
    # 仅在直接运行时使用 Flask 开发服务器（不推荐生产环境）
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    print("⚠️ 警告: 正在使用 Flask 开发服务器")
    print("💡 生产环境请使用: gunicorn --config gunicorn.conf.py wsgi:application")
    app.run(host="0.0.0.0", port=port, debug=debug)
