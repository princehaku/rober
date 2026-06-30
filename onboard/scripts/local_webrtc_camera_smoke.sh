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

cleanup_stale_camera_listener() {
  # systemd restart 曾出现旧 python 进程脱离 unit 但继续占用 8088；只清理同脚本旧实例，避免误杀其它服务。
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
    if [[ "${cmdline}" != *"local_webrtc_camera_smoke.py"* ]]; then
      echo "camera port ${PORT} is occupied by non-camera process pid=${pid}: ${cmdline}" >&2
      continue
    fi
    # 先给旧服务正常退出机会；仍不退出时才 kill -9，避免 systemd 陷入端口占用重启循环。
    echo "cleanup stale local_webrtc_camera_smoke.py listener pid=${pid} on port ${PORT}" >&2
    kill "${pid}" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
      kill -0 "${pid}" 2>/dev/null || break
      sleep 0.2
    done
    kill -0 "${pid}" 2>/dev/null && kill -9 "${pid}" 2>/dev/null || true
  done
}

cleanup_stale_camera_listener

# 默认 auto 会跳过 Orange Pi 的 cedrus/metadata 节点，优先选择真实 UVC capture。
exec python3 "${SCRIPT_DIR}/local_webrtc_camera_smoke.py" \
  --host "${HOST}" \
  --port "${PORT}" \
  --video-source "${ROBER_CAMERA_SOURCE}" \
  --width "${WIDTH}" \
  --height "${HEIGHT}" \
  --fps "${FPS}"
