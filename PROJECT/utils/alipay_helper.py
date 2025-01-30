from alipay import AliPay
import os
import sys
import logging

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.alipay_config import ALIPAY_CONFIG

logger = logging.getLogger('mooc_app')

class AlipayHelper:
    def __init__(self):
        try:
            self.app_private_key = open(ALIPAY_CONFIG['app_private_key_path']).read()
            self.alipay_public_key = open(ALIPAY_CONFIG['alipay_public_key_path']).read()
            
            logger.info("正在初始化支付宝配置")
            logger.info(f"APP_ID: {ALIPAY_CONFIG['app_id']}")
            logger.info(f"私钥路径: {ALIPAY_CONFIG['app_private_key_path']}")
            logger.info(f"公钥路径: {ALIPAY_CONFIG['alipay_public_key_path']}")
            
            self.alipay = AliPay(
                appid=ALIPAY_CONFIG['app_id'],
                app_notify_url=ALIPAY_CONFIG['notify_url'],
                app_private_key_string=self.app_private_key,
                alipay_public_key_string=self.alipay_public_key,
                sign_type=ALIPAY_CONFIG['sign_type'],
                debug=ALIPAY_CONFIG['debug']
            )
            logger.info("支付宝配置初始化成功")
        except Exception as e:
            logger.error(f"支付宝配置初始化失败: {str(e)}", exc_info=True)
            raise
    
    def create_order(self, order_no, amount, subject):
        """创建支付宝订单"""
        try:
            order_string = self.alipay.api_alipay_trade_page_pay(
                out_trade_no=order_no,
                total_amount=str(amount),
                subject=subject,
                return_url=ALIPAY_CONFIG['return_url'],
                notify_url=ALIPAY_CONFIG['notify_url']
            )
            # 使用沙箱环境网关
            if ALIPAY_CONFIG['debug']:
                return f"https://openapi-sandbox.dl.alipaydev.com/gateway.do?{order_string}"
            else:
                return f"https://openapi.alipay.com/gateway.do?{order_string}"
        except Exception as e:
            logger.error(f"创建支付宝订单失败: {str(e)}", exc_info=True)
            raise
    
    def verify_payment(self, data):
        """验证支付宝异步通知"""
        try:
            logger.info("开始验证支付宝回调参数")
            # 移除sign和sign_type参数
            signature = data.pop('sign', None)
            sign_type = data.pop('sign_type', None)
            if not signature:
                logger.error("回调参数中缺少签名")
                return False
                
            logger.info(f"签名类型: {sign_type}, 签名值: {signature}")
            logger.info(f"待验证参数: {data}")
            
            # 验证签名
            success = self.alipay.verify(data, signature)
            logger.info(f"签名验证结果: {success}")
            
            # 恢复sign和sign_type参数
            data['sign'] = signature
            if sign_type:
                data['sign_type'] = sign_type
                
            return success
        except Exception as e:
            logger.error(f"验证支付宝回调时发生错误: {str(e)}", exc_info=True)
            return False 