#!/bin/bash

# 设置日志文件
DEPLOY_LOG="logs/system/deploy.log"
mkdir -p logs/system

# 记录日志的函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$DEPLOY_LOG"
}

# 确保目录存在
mkdir -p instance
mkdir -p logs/{app,tasks,system}
mkdir -p mooc_configs
mkdir -p mooc_executable

# 安装依赖
log "开始安装依赖..."
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    log "依赖安装失败"
    exit 1
fi
log "依赖安装完成"

# 初始化数据库
log "初始化数据库..."
python3 init_db.py
if [ $? -ne 0 ]; then
    log "数据库初始化失败"
    exit 1
fi
log "数据库初始化完成"

# 设置文件权限
log "设置文件权限..."
chmod -R 755 .
chmod -R 777 logs
chmod -R 777 instance
chmod -R 777 mooc_configs

# 启动应用
log "启动应用..."
pkill -f gunicorn
gunicorn -c gunicorn.conf.py app:app

log "部署完成" 