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

cleanup_stale_upper_api_listener() {
  # systemd 重启时可能遇到旧 upper_robot_api.py 脱离 unit 但继续占用 8787；只清同脚本旧实例。
  command -v ss >/dev/null 2>&1 || return 0
  local stale_pids=()
  local pid
  while IFS= read -r pid; do
    [[ -n "${pid}" ]] && stale_pids+=("${pid}")
  done < <(
    ss -ltnp 2>/dev/null \
      | awk -v port=":${PORT}" '$4 ~ port { print $0 }' \
      | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p' \
      | sort -u
  )
  for pid in "${stale_pids[@]}"; do
    [[ "${pid}" == "$$" ]] && continue
    local cmdline=""
    if [[ -r "/proc/${pid}/cmdline" ]]; then
      cmdline="$(tr '\0' ' ' <"/proc/${pid}/cmdline" | head -c 400)"
    fi
    if [[ "${cmdline}" != *"upper_robot_api.py"* ]]; then
      echo "upper api port ${PORT} is occupied by non-upper-api process pid=${pid}: ${cmdline}" >&2
      continue
    fi
    # 先温和退出旧 API；还不退出时再 kill -9，避免 systemd 被端口占用反复重启。
    echo "cleanup stale upper_robot_api.py listener pid=${pid} on port ${PORT}" >&2
    kill "${pid}" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
      kill -0 "${pid}" 2>/dev/null || break
      sleep 0.2
    done
    kill -0 "${pid}" 2>/dev/null && kill -9 "${pid}" 2>/dev/null || true
  done
}

cleanup_stale_upper_api_listener

exec python3 "${SCRIPT_DIR}/upper_robot_api.py" \
  --host "${HOST}" \
  --port "${PORT}" \
  --camera-base-url "${ROBER_CAMERA_BASE_URL}" \
  --base-port "${ROBER_BASE_SERIAL_PORT}" \
  --base-baudrate "${ROBER_BASE_BAUDRATE}" \
  --max-speed "${ROBER_BASE_MAX_SPEED}"
