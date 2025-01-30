from flask import Flask
from extensions import db
from models import User, Task, Order
import os

app = Flask(__name__)

# 确保实例目录存在
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "app.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

if __name__ == '__main__':
    with app.app_context():
        # 删除所有表（如果存在）
        db.drop_all()
        # 创建所有表
        db.create_all()
        print("数据库表已成功创建！") 