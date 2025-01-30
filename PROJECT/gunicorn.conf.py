import multiprocessing
import os

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 绑定地址
bind = '127.0.0.1:8000'

# 工作模式
worker_class = 'sync'

# 最大请求数
max_requests = 2000
max_requests_jitter = 400

# 超时时间
timeout = 30

# 日志配置
accesslog = os.path.join('logs', 'gunicorn_access.log')
errorlog = os.path.join('logs', 'gunicorn_error.log')
loglevel = 'info'

# 进程名称
proc_name = 'mooc_web'

# 守护进程
daemon = True

# 用户组
user = None  # 在生产环境中设置适当的用户
group = None  # 在生产环境中设置适当的用户组 