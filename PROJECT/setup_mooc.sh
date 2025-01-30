#!/bin/bash

# 设置日志文件
LOG_FILE="logs/system/setup.log"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 记录开始时间
echo "Setup started at $(date)" > "$LOG_FILE"

# 检查mooc可执行文件
MOOC_EXE="../mooc-1.3.2/aoaostar_mooc"
if [ ! -f "$MOOC_EXE" ]; then
    echo "Error: MOOC executable not found at $MOOC_EXE" | tee -a "$LOG_FILE"
    exit 1
fi

# 检查文件权限
if [ ! -x "$MOOC_EXE" ]; then
    echo "Setting executable permission for $MOOC_EXE" | tee -a "$LOG_FILE"
    chmod +x "$MOOC_EXE"
fi

# 创建必要的目录
echo "Creating necessary directories..." | tee -a "$LOG_FILE"
mkdir -p mooc_configs
mkdir -p logs/tasks
mkdir -p logs/app
mkdir -p logs/system
mkdir -p instance

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed" | tee -a "$LOG_FILE"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed" | tee -a "$LOG_FILE"
    exit 1
fi

# 安装Python依赖
echo "Installing Python dependencies..." | tee -a "$LOG_FILE"
pip3 install -r requirements.txt >> "$LOG_FILE" 2>&1

# 初始化数据库
echo "Initializing database..." | tee -a "$LOG_FILE"
python3 init_db.py >> "$LOG_FILE" 2>&1

# 记录完成时间
echo "Setup completed at $(date)" | tee -a "$LOG_FILE" 