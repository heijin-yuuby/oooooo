from app import app, db
import os

# 确保实例目录存在
os.makedirs('instance', exist_ok=True)

# 在应用上下文中创建数据库
with app.app_context():
    db.create_all()
    print("Database initialized successfully.")
