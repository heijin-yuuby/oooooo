FROM ubuntu:latest

WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装必要的依赖
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制可执行文件
COPY aoaostar_mooc /app/
RUN chmod +x /app/aoaostar_mooc

# 创建配置和日志目录
RUN mkdir -p /app/configs /app/logs

# 设置入口点
ENTRYPOINT ["/app/aoaostar_mooc"]
CMD ["-h"] 