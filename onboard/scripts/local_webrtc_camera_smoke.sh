#!/usr/bin/env bash
set -euo pipefail

# 这个启动脚本只封装本地 WebRTC 摄像头 smoke，不碰 ROS2、串口或底盘控制。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-8088}"
HOST="${HOST:-0.0.0.0}"
VIDEO_SOURCE="${ROBER_CAMERA_SOURCE:-0}"
WIDTH="${WIDTH:-640}"
HEIGHT="${HEIGHT:-480}"
FPS="${FPS:-15}"

# 自检模式只访问已经启动的 HTTP/WebRTC smoke，不启动 ROS2/串口/底盘控制。
if [[ -n "${ROBER_WEBRTC_SELF_TEST_URL:-}" ]]; then
  exec python3 "${SCRIPT_DIR}/local_webrtc_camera_smoke.py" \
    --self-test-url "${ROBER_WEBRTC_SELF_TEST_URL}" \
    --self-test-timeout "${ROBER_WEBRTC_SELF_TEST_TIMEOUT:-8}" \
    ${ROBER_WEBRTC_REQUIRE_FRAME:+--require-frame}
fi

# 依赖安装交给现场同学显式处理；脚本本身即使缺依赖也能启动诊断页。
exec python3 "${SCRIPT_DIR}/local_webrtc_camera_smoke.py" \
  --host "${HOST}" \
  --port "${PORT}" \
  --video-source "${VIDEO_SOURCE}" \
  --width "${WIDTH}" \
  --height "${HEIGHT}" \
  --fps "${FPS}"
