#!/usr/bin/env bash
# O1 LiDAR lifecycle：把 PC/API 的 start/stop 映射成受管 ROS2 LiDAR runtime。
# 本脚本只管理自己创建的进程组，避免 stop 误杀上位机其他 ROS2 任务。
# 雷达串口与底盘 UART 必须隔离；/dev/ttyS5 被显式拒绝。

set -Eeuo pipefail

ACTION="${1:-}"
if [[ $# -gt 0 ]]; then
  shift
fi

ONBOARD_ROOT="/root/rober/onboard"
SERIAL_PORT="/dev/ttyACM0"
SERIAL_BAUDRATE="150000"
FRAME_ID="laser_frame"
RUNTIME_DIR="${ROBER_LIDAR_RUNTIME_DIR:-/tmp/rober_lidar_lifecycle}"
LOG_DIR=""
DRIVER_PID=""
TF_PID=""
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

usage() {
  cat <<'USAGE'
Usage: o1_lidar_lifecycle.sh start|stop|status [options]

Options:
  --onboard-root PATH    onboard workspace path, default /root/rober/onboard
  --serial-port PATH     LiDAR serial path, default /dev/ttyACM0
  --serial-baudrate N    LiDAR baudrate, default 150000
  --frame-id NAME        LiDAR frame id, default laser_frame
  --runtime-dir PATH     state/log root, default /tmp/rober_lidar_lifecycle
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
    --runtime-dir)
      RUNTIME_DIR="$2"
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

PID_FILE="$RUNTIME_DIR/lidar_lifecycle.pid"
STATUS_FILE="$RUNTIME_DIR/lidar_lifecycle_status.json"
LOG_DIR="$RUNTIME_DIR/logs"
MANAGER_LOG="$LOG_DIR/lidar_lifecycle_manager.log"
DRIVER_LOG="$LOG_DIR/lidar_driver.log"
TF_LOG="$LOG_DIR/tf_static.log"
DRIVER_PID_FILE="$RUNTIME_DIR/lidar_driver.pid"
TF_PID_FILE="$RUNTIME_DIR/tf_static.pid"
START_CONFIRM_TIMEOUT_S="${ROBER_LIDAR_START_CONFIRM_TIMEOUT_S:-4}"

json_status() {
  # 状态 JSON 由 python 生成，避免 shell 手写转义把路径里的特殊字符写坏。
  local running="$1"
  local pid="$2"
  local state="$3"
  local message="$4"
  python3 - "$running" "$pid" "$state" "$message" "$SERIAL_PORT" "$SERIAL_BAUDRATE" "$FRAME_ID" "$RUNTIME_DIR" "$LOG_DIR" <<'PY'
import json
import sys
import time

running, pid, state, message, serial_port, baudrate, frame_id, runtime_dir, log_dir = sys.argv[1:10]
payload = {
    "schema": "trashbot.o1.lidar_lifecycle.v1",
    "generated_at_ms": int(time.time() * 1000),
    "running": running == "true",
    "pid": int(pid) if pid.isdigit() else None,
    "state": state,
    "message": message,
    "serial_port": serial_port,
    "baudrate": int(baudrate) if baudrate.isdigit() else baudrate,
    "frame_id": frame_id,
    "runtime_dir": runtime_dir,
    "log_dir": log_dir,
    "driver": "ros2_trashbot_hardware lidar_driver",
    "static_tf": "base_link -> laser_frame",
    "sends_base_motion_commands": False,
    "uses_base_uart": False,
    "publishes_cmd_vel": False,
    "blocked_base_uart": "/dev/ttyS5",
    "blocked_commands_not_sent": ["T=1", "T=13", "T=130", "T=131", "/cmd_vel", "/api/base/manual"],
}
print(json.dumps(payload, ensure_ascii=False))
PY
}

write_status_file() {
  # status 文件用于 API/SSH 复盘；HTTP start/stop 仍以命令退出码为准。
  mkdir -p "$RUNTIME_DIR" "$LOG_DIR"
  json_status "$@" >"$STATUS_FILE"
}

emit_status_file_or_fallback() {
  # start 需要把 manager 写下的失败原因原样带回 HTTP stdout，方便 PC 显示根因。
  if [[ -s "$STATUS_FILE" ]]; then
    cat "$STATUS_FILE"
  else
    json_status "$@"
  fi
}

status_file_state() {
  # 用 python 读 JSON，避免 shell 对中文 message 或路径字符做脆弱切分。
  python3 - "$STATUS_FILE" <<'PY'
import json
import sys
from pathlib import Path

try:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except Exception:
    print("")
else:
    print(str(payload.get("state") or ""))
PY
}

source_ros_setups() {
  # ROS2 setup 脚本可能依赖未定义变量，source 阶段临时关闭 nounset。
  set +u
  source /opt/ros/humble/setup.bash
  source "$ONBOARD_ROOT/install/setup.bash"
  set -u
}

guard_safety() {
  # 先硬拒绝底盘 UART，防止通配或 by-path 规则误放行 WAVE ROVER。
  if [[ "$SERIAL_PORT" == "/dev/ttyS5" ]]; then
    echo "refusing WAVE ROVER base UART /dev/ttyS5" >&2
    exit 41
  fi
  # 只允许 LiDAR-looking 路径；真实现场当前为 /dev/ttyACM0 和 STC USB Serial。
  case "$SERIAL_PORT" in
    /dev/ttyACM*|/dev/lidar|/dev/serial/by-id/*STC*|/dev/serial/by-id/*stc*|/dev/serial/by-path/*)
      ;;
    *)
      echo "refusing non-LiDAR-looking serial port: $SERIAL_PORT" >&2
      exit 40
      ;;
  esac
}

pid_is_ours() {
  # 只承认由本脚本 __run 子命令创建的 manager，stop 不按名称扫杀 ROS2。
  local pid="$1"
  if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
    return 1
  fi
  if [[ -r "/proc/$pid/cmdline" ]]; then
    tr '\0' ' ' <"/proc/$pid/cmdline" | grep -F "$(basename "$SCRIPT_PATH") __run" >/dev/null
    return $?
  fi
  ps -p "$pid" -o command= 2>/dev/null | grep -F "$(basename "$SCRIPT_PATH") __run" >/dev/null
}

current_pid() {
  # pid 文件不存在时返回空字符串，status 仍要输出结构化 JSON。
  if [[ -f "$PID_FILE" ]]; then
    tr -dc '0-9' <"$PID_FILE"
  fi
}

is_running() {
  local pid
  pid="$(current_pid)"
  [[ -n "$pid" ]] && pid_is_ours "$pid"
}

require_runtime() {
  # start 进入后台 manager 后再检查 runtime，让 API 快速拿到明确失败日志。
  test -f /opt/ros/humble/setup.bash
  test -f "$ONBOARD_ROOT/install/setup.bash"
  test -e "$SERIAL_PORT"
  source_ros_setups
  command -v ros2 >/dev/null
}

cleanup_children() {
  # driver 先收到 SIGTERM，给它机会发送 LiDAR stop bytes 并关闭串口。
  if [[ -n "${DRIVER_PID:-}" ]] && kill -0 "$DRIVER_PID" 2>/dev/null; then
    kill "$DRIVER_PID" 2>/dev/null || true
    wait "$DRIVER_PID" 2>/dev/null || true
  fi
  if [[ -n "${TF_PID:-}" ]] && kill -0 "$TF_PID" 2>/dev/null; then
    kill "$TF_PID" 2>/dev/null || true
    wait "$TF_PID" 2>/dev/null || true
  fi
  rm -f "$DRIVER_PID_FILE" "$TF_PID_FILE"
}

run_manager() {
  # manager 是独立进程组根；stop 只 kill 这个进程组。
  local final_status_written="false"
  on_manager_exit() {
    local rc="$?"
    cleanup_children
    if [[ "$final_status_written" != "true" && "$rc" -ne 0 ]]; then
      write_status_file false "$$" "failed" "LiDAR lifecycle manager failed with rc=$rc; see logs"
    fi
    return "$rc"
  }
  trap on_manager_exit EXIT
  trap cleanup_children INT TERM
  mkdir -p "$RUNTIME_DIR" "$LOG_DIR"
  echo "$$" >"$PID_FILE"
  write_status_file true "$$" "starting" "LiDAR lifecycle manager starting"
  guard_safety
  require_runtime

  # 静态 TF 与 driver 分进程启动，便于日志和故障定位分开查看。
  ros2 run tf2_ros static_transform_publisher \
    --x 0 --y 0 --z 0 --roll 0 --pitch 0 --yaw 0 \
    --frame-id base_link --child-frame-id "$FRAME_ID" \
    >"$TF_LOG" 2>&1 &
  TF_PID="$!"
  echo "$TF_PID" >"$TF_PID_FILE"

  # lidar_driver 只打开 LiDAR 串口；参数不包含底盘 UART 或任何 cmd_vel 发布。
  ros2 run ros2_trashbot_hardware lidar_driver --ros-args \
    -p serial_port:="$SERIAL_PORT" \
    -p serial_baudrate:="$SERIAL_BAUDRATE" \
    -p frame_id:="$FRAME_ID" \
    -p publish_raw_packets:=true \
    >"$DRIVER_LOG" 2>&1 &
  DRIVER_PID="$!"
  echo "$DRIVER_PID" >"$DRIVER_PID_FILE"

  write_status_file true "$$" "running" "LiDAR lifecycle manager running"
  set +e
  wait "$DRIVER_PID"
  local driver_rc="$?"
  set -e
  final_status_written="true"
  write_status_file false "$$" "failed" "LiDAR driver exited with rc=$driver_rc; see $DRIVER_LOG"
  rm -f "$PID_FILE"
  return "$driver_rc"
}

start_runtime() {
  guard_safety
  mkdir -p "$RUNTIME_DIR" "$LOG_DIR"
  if is_running; then
    json_status true "$(current_pid)" "running" "LiDAR lifecycle already running"
    exit 0
  fi
  if ! command -v setsid >/dev/null 2>&1; then
    echo "setsid is required to isolate LiDAR lifecycle process group" >&2
    exit 42
  fi
  # 用 setsid 创建独立进程组，stop 后续只杀这个 pid 对应的进程组。
  setsid bash "$SCRIPT_PATH" __run \
    --onboard-root "$ONBOARD_ROOT" \
    --serial-port "$SERIAL_PORT" \
    --serial-baudrate "$SERIAL_BAUDRATE" \
    --frame-id "$FRAME_ID" \
    --runtime-dir "$RUNTIME_DIR" \
    >"$MANAGER_LOG" 2>&1 &
  local manager_pid="$!"
  echo "$manager_pid" >"$PID_FILE"
  write_status_file true "$manager_pid" "starting" "LiDAR lifecycle start requested"
  # 等 manager 完成 ROS setup、串口打开和 driver 首轮存活确认，避免 HTTP 假成功。
  local deadline_ms
  deadline_ms="$(python3 - "$START_CONFIRM_TIMEOUT_S" <<'PY'
import sys
import time
print(int((time.time() + max(0.5, float(sys.argv[1]))) * 1000))
PY
)"
  while true; do
    local now_ms_value
    now_ms_value="$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)"
    if ! kill -0 "$manager_pid" 2>/dev/null; then
      emit_status_file_or_fallback false "" "failed" "LiDAR lifecycle manager exited during start confirmation"
      exit 43
    fi
    local state
    state="$(status_file_state)"
    if [[ "$state" == "failed" ]]; then
      emit_status_file_or_fallback false "" "failed" "LiDAR lifecycle manager reported failure during start confirmation"
      exit 43
    fi
    if [[ "$state" == "running" ]]; then
      # driver 可能在首个 read tick 才暴露断连/抢占；短暂确认能抓住这类瞬时失败。
      sleep 1
      if kill -0 "$manager_pid" 2>/dev/null && [[ "$(status_file_state)" == "running" ]]; then
        emit_status_file_or_fallback true "$manager_pid" "running" "LiDAR lifecycle manager running"
        exit 0
      fi
      emit_status_file_or_fallback false "" "failed" "LiDAR lifecycle manager stopped after initial running state"
      exit 43
    fi
    if [[ "$now_ms_value" -ge "$deadline_ms" ]]; then
      emit_status_file_or_fallback true "$manager_pid" "starting" "LiDAR lifecycle start confirmation timed out"
      exit 44
    fi
    sleep 0.1
  done
}

stop_runtime() {
  local pid
  pid="$(current_pid)"
  if [[ -z "$pid" ]] || ! pid_is_ours "$pid"; then
    rm -f "$PID_FILE"
    write_status_file false "" "stopped" "LiDAR lifecycle was not running"
    json_status false "" "stopped" "LiDAR lifecycle was not running"
    exit 0
  fi
  # 只向受管进程组发 SIGTERM，不按 ros2/lidar_driver 名称清理外部进程。
  kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  for _ in {1..30}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 0.1
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
  write_status_file false "" "stopped" "LiDAR lifecycle stopped"
  json_status false "" "stopped" "LiDAR lifecycle stopped"
}

status_runtime() {
  local pid
  pid="$(current_pid)"
  if [[ -n "$pid" ]] && pid_is_ours "$pid"; then
    json_status true "$pid" "running" "LiDAR lifecycle running"
  else
    json_status false "" "stopped" "LiDAR lifecycle not running"
  fi
}

case "$ACTION" in
  start)
    start_runtime
    ;;
  stop)
    stop_runtime
    ;;
  status)
    status_runtime
    ;;
  __run)
    run_manager
    ;;
  -h|--help|"")
    usage
    ;;
  *)
    echo "unknown action: $ACTION" >&2
    usage >&2
    exit 2
    ;;
esac
