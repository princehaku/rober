#!/usr/bin/env bash
set -euo pipefail

# 该脚本只启动本地摄像头 HTTP/WebRTC smoke，不启动 ROS2、串口、Nav2 或底盘控制。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8088}"
ROBER_CAMERA_SOURCE="${ROBER_CAMERA_SOURCE:-auto}"
WIDTH="${WIDTH:-640}"
HEIGHT="${HEIGHT:-480}"
FPS="${FPS:-15}"

# 默认 auto 会跳过 Orange Pi 的 cedrus/metadata 节点，优先选择真实 UVC capture。
exec python3 "${SCRIPT_DIR}/local_webrtc_camera_smoke.py" \
  --host "${HOST}" \
  --port "${PORT}" \
  --video-source "${ROBER_CAMERA_SOURCE}" \
  --width "${WIDTH}" \
  --height "${HEIGHT}" \
  --fps "${FPS}"
