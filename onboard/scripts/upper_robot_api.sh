#!/usr/bin/env bash
set -euo pipefail

# 上位机统一 API：只收敛 camera/radar/base HTTP 入口，不启动 ROS2/Nav2。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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
