import os

# 获取项目根目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 支付宝配置
ALIPAY_CONFIG = {
    'app_id': '9021000143667423',  # 从沙箱环境获取的APPID
    'app_private_key_path': os.path.join(BASE_DIR, 'config/keys/app_private_key.pem'),  # 应用私钥
    'alipay_public_key_path': os.path.join(BASE_DIR, 'config/keys/alipay_public_key.pem'),  # 支付宝公钥
    'notify_url': 'http://127.0.0.1:20086/api/alipay/notify',  # 本地测试回调地址
    'return_url': 'http://127.0.0.1:20086/api/alipay/return',  # 本地测试返回地址
    'sign_type': 'RSA2',
    'debug': True  # 开启沙箱模式
} 