#!/usr/bin/env bash
set -euo pipefail

# 统一上位机 API 的 systemd 入口；这里负责补齐 ROS2 运行环境。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ONBOARD_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# FastDDS SHM 在 Orange Pi 上容易残留锁文件；PC 键盘手控必须优先稳定低延迟。
export RMW_FASTRTPS_USE_SHM="${RMW_FASTRTPS_USE_SHM:-0}"

# ROS setup 脚本可能读取未定义变量，source 时临时关闭 nounset，避免 systemd 直接退出。
if [ -f /opt/ros/humble/setup.bash ]; then
  set +u
  source /opt/ros/humble/setup.bash
  set -u
fi

# 工作区 overlay 让进程内 rclpy publisher 能直接加载本项目消息和依赖。
if [ -f "${ONBOARD_ROOT}/install/setup.bash" ]; then
  set +u
  source "${ONBOARD_ROOT}/install/setup.bash"
  set -u
fi

# 现场固定参数仍允许 systemd Environment 覆盖，避免把端口或串口写散。
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8787}"
ROBER_CAMERA_BASE_URL="${ROBER_CAMERA_BASE_URL:-http://127.0.0.1:8088}"
ROBER_BASE_SERIAL_PORT="${ROBER_BASE_SERIAL_PORT:-/dev/ttyS5}"
ROBER_BASE_BAUDRATE="${ROBER_BASE_BAUDRATE:-115200}"
ROBER_BASE_MAX_SPEED="${ROBER_BASE_MAX_SPEED:-0.12}"

exec python3 "${SCRIPT_DIR}/upper_robot_api.py" \
  --host "${HOST}" \
  --port "${PORT}" \
  --camera-base-url "${ROBER_CAMERA_BASE_URL}" \
  --base-port "${ROBER_BASE_SERIAL_PORT}" \
  --base-baudrate "${ROBER_BASE_BAUDRATE}" \
  --max-speed "${ROBER_BASE_MAX_SPEED}"
