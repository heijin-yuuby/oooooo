import os

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-please-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
    
    # 日志配置
    LOG_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs')
    APP_LOG_FILE = os.path.join(LOG_DIR, 'app', 'web_app.log')
    TASK_LOG_DIR = os.path.join(LOG_DIR, 'tasks')
    SYSTEM_LOG_DIR = os.path.join(LOG_DIR, 'system')
    
    # MOOC配置
    MOOC_CONFIG_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'mooc_configs')
    MOOC_EXECUTABLE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'mooc_executable')
    
    # 系统配置
    MAX_TASKS = 50  # 最大并发任务数
    
    @staticmethod
    def init_app(app):
        # 确保必要的目录存在
        os.makedirs(os.path.join(Config.LOG_DIR, 'app'), exist_ok=True)
        os.makedirs(Config.TASK_LOG_DIR, exist_ok=True)
        os.makedirs(Config.SYSTEM_LOG_DIR, exist_ok=True)
        os.makedirs(Config.MOOC_CONFIG_DIR, exist_ok=True)
        os.makedirs('instance', exist_ok=True) 