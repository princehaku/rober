FROM python:3.12-slim

# 这个镜像只承载 independent relay proof，避免把 ROS2/Humble 构建链路拉进云入口验证。
WORKDIR /app

# cloud-relay/src 提供部署入口；onboard behavior 包继续提供唯一协议实现，避免复制第二套语义。
# 构建 context 仍为仓库根，这样镜像能同时拿到 cloud-relay 入口和复用的纯 Python relay 模块。
COPY cloud-relay/src /app/cloud-relay/src
COPY onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior /app/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior

# /data 用于 file-backed proof store；生产云仍需要数据库或队列替代这个本地文件。
RUN adduser --disabled-password --gecos "" relay \
    && mkdir -p /data \
    && chown -R relay:relay /app /data

USER relay
ENV PYTHONPATH=/app/cloud-relay/src:/app/onboard/src/ros2_trashbot_behavior \
    TRASHBOT_REMOTE_CLOUD_HOST=0.0.0.0 \
    TRASHBOT_REMOTE_CLOUD_PORT=8088 \
    TRASHBOT_REMOTE_CLOUD_STATE=/data/remote_cloud_relay_state.json

EXPOSE 8088

CMD ["python", "-m", "ros2_trashbot_cloud_relay.remote_cloud_relay"]
