# 使用 Ubuntu 作为基础镜像
FROM ubuntu:latest

# 设置工作目录
WORKDIR /workspace

# 安装依赖和根证书
RUN apt update && apt install -y ca-certificates && update-ca-certificates

# 复制程序文件和配置文件
COPY aoaostar_mooc /workspace/aoaostar_mooc
COPY config.json /workspace/config.json
COPY view /workspace/view

# 设置可执行权限
RUN chmod +x /workspace/aoaostar_mooc

# 运行程序
CMD ["/workspace/aoaostar_mooc", "--config", "/workspace/config.json"]