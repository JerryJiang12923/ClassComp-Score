import os

bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = 1  # Render 免费版内存限制，使用单个 worker
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# 日志配置
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 内存优化
worker_tmp_dir = "/dev/shm"  # 使用内存文件系统提升性能

# 优雅关闭
graceful_timeout = 30
