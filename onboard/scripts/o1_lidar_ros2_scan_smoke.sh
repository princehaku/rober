#!/usr/bin/env bash
# O1 LiDAR-only ROS2 smoke：启动 LiDAR driver 和静态 TF，采集 /scan、raw packet、TF。
# 安全边界：只允许 LiDAR 串口 /dev/ttyACM0 或 /dev/lidar；绝不写 /dev/ttyS5。
# 本脚本不发布 /cmd_vel，不调用 /api/base/manual，不发送 WAVE ROVER T 命令。

set -Eeuo pipefail

ONBOARD_ROOT="/root/rober/onboard"
SERIAL_PORT="/dev/ttyACM0"
SERIAL_BAUDRATE="230400"
FRAME_ID="laser_frame"
OUTPUT_DIR="/tmp/o1_lidar_ros2_scan_smoke"
DRIVER_PID=""
TF_PID=""

usage() {
  cat <<'USAGE'
Usage: o1_lidar_ros2_scan_smoke.sh [options]

Options:
  --onboard-root PATH    onboard workspace path, default /root/rober/onboard
  --serial-port PATH     LiDAR serial path, default /dev/ttyACM0
  --serial-baudrate N    LiDAR baudrate, default 230400
  --frame-id NAME        LiDAR frame id, default laser_frame
  --output-dir PATH      evidence output dir, default /tmp/o1_lidar_ros2_scan_smoke
  -h, --help             show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --onboard-root)
      ONBOARD_ROOT="$2"
      shift 2
      ;;
    --serial-port)
      SERIAL_PORT="$2"
      shift 2
      ;;
    --serial-baudrate)
      SERIAL_BAUDRATE="$2"
      shift 2
      ;;
    --frame-id)
      FRAME_ID="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

log() {
  printf '[o1-lidar-smoke] %s\n' "$*"
}

source_ros_setups() {
  # ROS2/colcon 生成的 setup 脚本会访问未定义变量；只在 source 阶段放宽 nounset。
  set +u
  source /opt/ros/humble/setup.bash
  source "$ONBOARD_ROOT/install/setup.bash"
  set -u
}

cleanup() {
  # 退出时先停 driver，让 Python driver best-effort 发送 LiDAR stop bytes 并关闭串口。
  if [[ -n "${DRIVER_PID:-}" ]] && kill -0 "$DRIVER_PID" 2>/dev/null; then
    kill "$DRIVER_PID" 2>/dev/null || true
    wait "$DRIVER_PID" 2>/dev/null || true
  fi
  if [[ -n "${TF_PID:-}" ]] && kill -0 "$TF_PID" 2>/dev/null; then
    kill "$TF_PID" 2>/dev/null || true
    wait "$TF_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

guard_safety() {
  # /dev/ttyS5 是 WAVE ROVER 底盘 UART，必须先于通配规则显式拒绝。
  if [[ "$SERIAL_PORT" == "/dev/ttyS5" ]]; then
    echo "refusing WAVE ROVER base UART /dev/ttyS5" >&2
    exit 41
  fi
  # 只允许 LiDAR 设备名，防止误把底盘 UART 当雷达打开。
  case "$SERIAL_PORT" in
    /dev/ttyACM*|/dev/lidar|/dev/serial/by-id/*STC*|/dev/serial/by-id/*stc*|/dev/serial/by-path/*)
      ;;
    *)
      echo "refusing non-LiDAR-looking serial port: $SERIAL_PORT" >&2
      exit 40
      ;;
  esac
}

require_runtime() {
  # runtime 必须已经安装并构建；缺任何一项都退出，让 bootstrap 脚本先补齐。
  test -f /opt/ros/humble/setup.bash
  test -f "$ONBOARD_ROOT/install/setup.bash"
  test -e "$SERIAL_PORT"
  source_ros_setups
  command -v ros2 >/dev/null
}

collect_topics() {
  mkdir -p "$OUTPUT_DIR"
  log "output_dir=$OUTPUT_DIR"
  log "serial_port=$SERIAL_PORT baudrate=$SERIAL_BAUDRATE frame_id=$FRAME_ID"

  # static TF 与 driver 分开启动，避免 learn.launch.py 顺带启动 SLAM/Nav 组件。
  timeout 60 ros2 run tf2_ros static_transform_publisher \
    --x 0 --y 0 --z 0 --roll 0 --pitch 0 --yaw 0 \
    --frame-id base_link --child-frame-id "$FRAME_ID" \
    >"$OUTPUT_DIR/tf_static.log" 2>&1 &
  TF_PID="$!"

  # 该 driver 只会对 LiDAR 串口发送 A5 60 和退出停止序列，不发送任何 WAVE ROVER T 命令。
  timeout 60 ros2 run ros2_trashbot_hardware lidar_driver --ros-args \
    -p serial_port:="$SERIAL_PORT" \
    -p serial_baudrate:="$SERIAL_BAUDRATE" \
    -p frame_id:="$FRAME_ID" \
    -p publish_raw_packets:=true \
    >"$OUTPUT_DIR/lidar_driver.log" 2>&1 &
  DRIVER_PID="$!"

  # 给串口和 discovery 留出短启动窗口；失败日志仍会被保留。
  sleep 5
  timeout 12 ros2 topic echo --once /scan >"$OUTPUT_DIR/scan_once.txt" 2>&1 || true
  timeout 12 ros2 topic hz /scan >"$OUTPUT_DIR/scan_hz.txt" 2>&1 || true
  timeout 12 ros2 topic echo --once /lidar/raw_packet >"$OUTPUT_DIR/raw_packet_once.txt" 2>&1 || true
  timeout 12 ros2 run tf2_ros tf2_echo base_link "$FRAME_ID" >"$OUTPUT_DIR/tf2_echo.txt" 2>&1 || true
  timeout 5 ros2 topic list >"$OUTPUT_DIR/topic_list.txt" 2>&1 || true
}

summarize() {
  # summary 只统计证据文件是否出现关键字，最终验收仍需人工看完整 artifact。
  python3 - "$OUTPUT_DIR" "$FRAME_ID" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
frame_id = sys.argv[2]


def read(name):
    path = out / name
    return path.read_text(errors="replace") if path.exists() else ""


summary = {
    "schema": "trashbot.o1.lidar_ros2_scan_smoke.v1",
    "output_dir": str(out),
    "required_observations": {
        "scan_once": {
            "topic": "/scan",
            "artifact_file": "scan_once.txt",
            "observed": "ranges:" in read("scan_once.txt"),
        },
        "scan_hz": {
            "topic": "/scan",
            "artifact_file": "scan_hz.txt",
            "observed": "average rate:" in read("scan_hz.txt"),
        },
        "raw_packet_once": {
            "topic": "/lidar/raw_packet",
            "artifact_file": "raw_packet_once.txt",
            "observed": "data:" in read("raw_packet_once.txt"),
        },
        "tf": {
            "parent_frame": "base_link",
            "child_frame": frame_id,
            "artifact_file": "tf2_echo.txt",
            "observed": "At time" in read("tf2_echo.txt") or "Translation:" in read("tf2_echo.txt"),
        },
    },
    "driver_log_tail": read("lidar_driver.log")[-2000:],
    "driver_started_by_smoke": True,
    "lidar_start_command_sent_by_smoke": True,
    "lidar_start_command_hex": "A5 60",
    "refuses_base_uart_ttyS5": True,
    "safe_to_control": False,
    "sends_base_motion_commands": False,
    "calls_base_manual": False,
    "publishes_cmd_vel": False,
}
summary["scan_once_observed"] = summary["required_observations"]["scan_once"]["observed"]
summary["scan_hz_observed"] = summary["required_observations"]["scan_hz"]["observed"]
summary["raw_packet_once_observed"] = summary["required_observations"]["raw_packet_once"]["observed"]
summary["tf_observed"] = summary["required_observations"]["tf"]["observed"]
summary["all_required_observations_observed"] = all(item["observed"] for item in summary["required_observations"].values())
(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY
}

main() {
  guard_safety
  require_runtime
  collect_topics
  summarize
}

main "$@"
