FROM python:3.12-slim

# 这个镜像只承载 independent relay proof，避免把 ROS2/Humble 构建链路拉进云入口验证。
WORKDIR /app

# relay 当前只依赖 Python 标准库；复制最小包目录可以降低镜像上下文和运行时耦合。
COPY src/ros2_trashbot_behavior/ros2_trashbot_behavior /app/ros2_trashbot_behavior

# /data 用于 file-backed proof store；生产云仍需要数据库或队列替代这个本地文件。
RUN adduser --disabled-password --gecos "" relay \
    && mkdir -p /data \
    && chown -R relay:relay /app /data

USER relay
ENV PYTHONPATH=/app \
    TRASHBOT_REMOTE_CLOUD_HOST=0.0.0.0 \
    TRASHBOT_REMOTE_CLOUD_PORT=8088 \
    TRASHBOT_REMOTE_CLOUD_STATE=/data/remote_cloud_relay_state.json

EXPOSE 8088

CMD ["python", "-m", "ros2_trashbot_behavior.remote_cloud_relay"]
