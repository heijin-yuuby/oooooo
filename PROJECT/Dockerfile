FROM alpine:latest

# 安装必要的库
RUN apk add --no-cache \
    libstdc++ \
    gcompat

WORKDIR /app

COPY mooc_executable/aoaostar_mooc /app/aoaostar_mooc
RUN chmod +x /app/aoaostar_mooc && \
    mkdir -p /app/logs && \
    chmod 777 /app/logs

ENTRYPOINT ["/app/aoaostar_mooc"] 