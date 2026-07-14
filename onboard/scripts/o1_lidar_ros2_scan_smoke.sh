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

collect_device_snapshot() {
  # 只检查 LiDAR 候选设备与持有进程，不触碰 WAVE ROVER `/dev/ttyS5`。
  local phase="$1"
  mkdir -p "$OUTPUT_DIR"
  python3 - "$OUTPUT_DIR" "$phase" "$SERIAL_PORT" "$SERIAL_BAUDRATE" <<'PY'
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

out = Path(sys.argv[1])
phase = sys.argv[2]
serial_port = sys.argv[3]
serial_baudrate = sys.argv[4]


def compact_error(exc):
    return {"type": type(exc).__name__, "message": str(exc)[:240]}


def describe(path):
    item = {
        "path": path,
        "exists": os.path.exists(path),
        "lexists": os.path.lexists(path),
        "is_symlink": os.path.islink(path),
        "realpath": None,
        "mode_octal": None,
        "uid": None,
        "gid": None,
        "error": None,
    }
    try:
        if item["lexists"]:
            item["realpath"] = os.path.realpath(path)
            stat_result = os.stat(path)
            item["mode_octal"] = oct(stat_result.st_mode & 0o7777)
            item["uid"] = stat_result.st_uid
            item["gid"] = stat_result.st_gid
    except OSError as exc:
        item["error"] = compact_error(exc)
    return item


def run_probe(command):
    try:
        completed = subprocess.run(command, check=False, text=True, capture_output=True, timeout=3)
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout_preview": completed.stdout[:2000],
            "stderr_preview": completed.stderr[:2000],
            "tool_present": shutil.which(command[0]) is not None,
        }
    except Exception as exc:
        return {"command": command, "returncode": None, "error": compact_error(exc)}


paths = []
for candidate in [serial_port, "/dev/lidar", "/dev/ttyACM0"]:
    if candidate not in paths:
        paths.append(candidate)
for pattern in ("/dev/serial/by-id/*STC*", "/dev/serial/by-id/*stc*", "/dev/serial/by-path/*"):
    for candidate in glob.glob(pattern):
        if candidate not in paths:
            paths.append(candidate)

devices = {path: describe(path) for path in paths}
processes = {}
for path, info in devices.items():
    if not info.get("exists"):
        continue
    processes[path] = {
        "lsof": run_probe(["lsof", "-nP", "--", path]),
        "fuser": run_probe(["fuser", "-v", path]),
    }

payload = {
    "schema": "trashbot.o1.lidar_device_snapshot.v1",
    "generated_at_ms": int(time.time() * 1000),
    "phase": phase,
    "serial_port": serial_port,
    "serial_baudrate": int(serial_baudrate) if str(serial_baudrate).isdigit() else serial_baudrate,
    "devices": devices,
    "processes": processes,
    "safe_to_control": False,
    "publishes_cmd_vel": False,
    "calls_base_manual": False,
    "uses_base_uart": False,
    "robot_control_executed": False,
    "route_execution_success": False,
    "delivery_success": False,
    "hil_pass": False,
}
(out / f"device_snapshot_{phase}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
PY
}

source_ros_setups() {
  # ROS2/colcon 生成的 setup 脚本会访问未定义变量；只在 source 阶段放宽 nounset。
  set +u
  source /opt/ros/humble/setup.bash
  source "$ONBOARD_ROOT/install/setup.bash"
  set -u
}

cleanup() {
  # 退出时按进程组停 driver，避免只杀 timeout wrapper 而留下 ros2/lidar_driver 子进程。
  stop_process_group "$DRIVER_PID"
  stop_process_group "$TF_PID"
}
trap cleanup EXIT

stop_process_group() {
  local pid="${1:-}"
  if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
    return 0
  fi
  kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
}

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

serial_holder_pids() {
  # 只检查本轮 LiDAR 串口；发现已有 holder 就 fail-closed，避免制造 multiple access。
  if command -v fuser >/dev/null 2>&1; then
    fuser "$SERIAL_PORT" 2>/dev/null | tr -cs '0-9' ' ' | sed 's/^ *//;s/ *$//'
  else
    true
  fi
}

collect_topics() {
  mkdir -p "$OUTPUT_DIR"
  log "output_dir=$OUTPUT_DIR"
  log "serial_port=$SERIAL_PORT baudrate=$SERIAL_BAUDRATE frame_id=$FRAME_ID"
  collect_device_snapshot before
  local holder_pids
  holder_pids="$(serial_holder_pids || true)"
  if [[ -n "$holder_pids" ]]; then
    printf '%s\n' "$holder_pids" >"$OUTPUT_DIR/preexisting_lidar_holder_pids.txt"
    echo "preexisting LiDAR holder on $SERIAL_PORT: $holder_pids" >&2
    return 45
  fi

  # static TF 与 driver 分开启动，避免 learn.launch.py 顺带启动 SLAM/Nav 组件。
  setsid timeout 60 ros2 run tf2_ros static_transform_publisher \
    --x 0 --y 0 --z 0 --roll 0 --pitch 0 --yaw 0 \
    --frame-id base_link --child-frame-id "$FRAME_ID" \
    >"$OUTPUT_DIR/tf_static.log" 2>&1 &
  TF_PID="$!"

  # 该 driver 只会对 LiDAR 串口发送 A5 60 和退出停止序列，不发送任何 WAVE ROVER T 命令。
  setsid timeout 60 ros2 run ros2_trashbot_hardware lidar_driver --ros-args \
    -p serial_port:="$SERIAL_PORT" \
    -p serial_baudrate:="$SERIAL_BAUDRATE" \
    -p frame_id:="$FRAME_ID" \
    -p publish_raw_packets:=true \
    -p diagnostics_path:="$OUTPUT_DIR/lidar_driver_diagnostics.json" \
    >"$OUTPUT_DIR/lidar_driver.log" 2>&1 &
  DRIVER_PID="$!"

  # 给串口和 discovery 留出短启动窗口；失败日志仍会被保留。
  sleep 5
  collect_device_snapshot during
  timeout 12 ros2 topic echo --once /scan >"$OUTPUT_DIR/scan_once.txt" 2>&1 || true
  timeout 12 ros2 topic hz /scan >"$OUTPUT_DIR/scan_hz.txt" 2>&1 || true
  timeout 12 ros2 topic echo --once /lidar/raw_packet >"$OUTPUT_DIR/raw_packet_once.txt" 2>&1 || true
  timeout 12 ros2 run tf2_ros tf2_echo base_link "$FRAME_ID" >"$OUTPUT_DIR/tf2_echo.txt" 2>&1 || true
  timeout 5 ros2 topic list >"$OUTPUT_DIR/topic_list.txt" 2>&1 || true
}

summarize() {
  # summary 只统计证据文件是否出现关键字，最终验收仍需人工看完整 artifact。
  python3 - "$OUTPUT_DIR" "$FRAME_ID" "$SERIAL_PORT" "$SERIAL_BAUDRATE" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
frame_id = sys.argv[2]
serial_port = sys.argv[3]
serial_baudrate = sys.argv[4]


def read(name):
    path = out / name
    return path.read_text(errors="replace") if path.exists() else ""

def load_json(name):
    path = out / name
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"load_error": {"type": type(exc).__name__, "message": str(exc)[:240]}}

driver_diagnostics = load_json("lidar_driver_diagnostics.json")
driver_serial = driver_diagnostics.get("serial", {}) if isinstance(driver_diagnostics, dict) else {}
driver_log_tail = read("lidar_driver.log")[-2000:]
preexisting_holder_pids = read("preexisting_lidar_holder_pids.txt").strip().split()
driver_started_by_smoke = not bool(preexisting_holder_pids)

summary = {
    "schema": "trashbot.o1.lidar_ros2_scan_smoke.v1",
    "output_dir": str(out),
    "serial_port": serial_port,
    "serial_baudrate": int(serial_baudrate) if str(serial_baudrate).isdigit() else serial_baudrate,
    "baudrate_probe": {
        "tested_baudrate": int(serial_baudrate) if str(serial_baudrate).isdigit() else serial_baudrate,
        "vendor_wave_rover_reference_baudrate": 230400,
        "historical_field_baudrate_candidate": 150000,
        "vendor_reference_source": "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
        "historical_field_source": "docs/hardware/board_sensor_stack_smoke.md",
    },
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
    "device_snapshots": {
        "before": load_json("device_snapshot_before.json"),
        "during": load_json("device_snapshot_during.json"),
        "after": load_json("device_snapshot_after.json"),
    },
    "driver_diagnostics": driver_diagnostics,
    "driver_log_tail": driver_log_tail,
    "preexisting_lidar_holder_detected": bool(preexisting_holder_pids),
    "preexisting_lidar_holder_pids": preexisting_holder_pids,
    "serial_exception_observed": bool(driver_serial.get("read_exception_count")) or "SerialException" in driver_log_tail,
    "serial_exception_type": driver_serial.get("last_exception_type"),
    "serial_exception_message_hint": driver_serial.get("last_exception_message_hint"),
    "empty_read_count": driver_serial.get("empty_read_count"),
    "raw_bytes_observed": driver_serial.get("raw_bytes_observed"),
    "bytes_read_total": driver_serial.get("bytes_read_total"),
    "last_chunk_preview_hex": driver_serial.get("last_chunk_preview_hex"),
    "packet_count_total": driver_serial.get("packet_count_total"),
    "published_raw_packet_count": (
        driver_diagnostics.get("runtime", {}).get("published_raw_packet_count")
        if isinstance(driver_diagnostics, dict) else None
    ),
    "published_scan_count": (
        driver_diagnostics.get("runtime", {}).get("published_scan_count")
        if isinstance(driver_diagnostics, dict) else None
    ),
    "driver_started_by_smoke": driver_started_by_smoke,
    "lidar_start_command_sent_by_smoke": driver_started_by_smoke,
    "lidar_start_command_hex": "A5 60" if driver_started_by_smoke else None,
    "blocked_reason": "preexisting_lidar_holder" if preexisting_holder_pids else None,
    "refuses_base_uart_ttyS5": True,
    "safe_to_control": False,
    "sends_base_motion_commands": False,
    "calls_base_manual": False,
    "publishes_cmd_vel": False,
    "uses_base_uart": False,
    "robot_control_executed": False,
    "route_execution_success": False,
    "delivery_success": False,
    "hil_pass": False,
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
  local collect_rc
  set +e
  collect_topics
  collect_rc="$?"
  set -e
  cleanup
  DRIVER_PID=""
  TF_PID=""
  collect_device_snapshot after
  summarize
  exit "$collect_rc"
}

main "$@"
