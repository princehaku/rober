FROM python:3.12-slim

# 这个镜像只承载 independent relay proof，避免把 ROS2/Humble 构建链路拉进云入口验证。
WORKDIR /app

# relay 当前只依赖 Python 标准库；从 onboard 工作区复制 behavior 包中的纯 Python 模块（与 colcon 无关）。
# 构建时 context 必须为仓库根（见 cloud-relay/docker-compose.yml），否则 COPY 路径找不到。
COPY onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior /app/ros2_trashbot_behavior

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
