#!/usr/bin/env bash
# O11 Nav2 lifecycle：把 PC/API 的 start/stop 映射成受管 Nav2 runtime。
# 本脚本只启动 autonomous.launch.py 的 nav2_stack_only 模式，不启动巡逻或任务编排节点。
# 运动仍必须由显式确认后的 /api/nav2/goal/execute 触发；start 本身不发送 goal。

set -Eeuo pipefail

ACTION="${1:-}"
if [[ $# -gt 0 ]]; then
  shift
fi

ONBOARD_ROOT="/root/rober/onboard"
MAP_FILE="/root/rober/onboard/runtime/maps/trashbot_map.yaml"
BASE_PORT="/dev/ttyS5"
BASE_BAUDRATE="115200"
COMMAND_MODE="ros"
RUNTIME_DIR="${ROBER_NAV2_RUNTIME_DIR:-/tmp/rober_nav2_lifecycle}"
START_CONFIRM_TIMEOUT_S="${ROBER_NAV2_START_CONFIRM_TIMEOUT_S:-8}"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

usage() {
  cat <<'USAGE'
Usage: o11_nav2_lifecycle.sh start|stop|status [options]

Options:
  --onboard-root PATH     onboard workspace path, default /root/rober/onboard
  --map-file PATH         Nav2 map yaml, default /root/rober/onboard/runtime/maps/trashbot_map.yaml
  --base-port PATH        WAVE ROVER UART, default /dev/ttyS5
  --base-baudrate N       WAVE ROVER UART baudrate, default 115200
  --command-mode MODE     esp32_bridge command mode, default ros
  --runtime-dir PATH      state/log root, default /tmp/rober_nav2_lifecycle
  -h, --help              show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --onboard-root)
      ONBOARD_ROOT="$2"
      shift 2
      ;;
    --map-file)
      MAP_FILE="$2"
      shift 2
      ;;
    --base-port)
      BASE_PORT="$2"
      shift 2
      ;;
    --base-baudrate)
      BASE_BAUDRATE="$2"
      shift 2
      ;;
    --command-mode)
      COMMAND_MODE="$2"
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

PID_FILE="$RUNTIME_DIR/nav2_lifecycle.pid"
STATUS_FILE="$RUNTIME_DIR/nav2_lifecycle_status.json"
LOG_DIR="$RUNTIME_DIR/logs"
MANAGER_LOG="$LOG_DIR/nav2_lifecycle_manager.log"
LAUNCH_LOG="$LOG_DIR/autonomous_nav2_stack_only.log"

json_status() {
  # 状态 JSON 统一由 python 生成，避免 shell 手写转义破坏中文和路径。
  local running="$1"
  local pid="$2"
  local state="$3"
  local message="$4"
  python3 - "$running" "$pid" "$state" "$message" "$ONBOARD_ROOT" "$MAP_FILE" "$BASE_PORT" "$BASE_BAUDRATE" "$COMMAND_MODE" "$RUNTIME_DIR" "$LOG_DIR" <<'PY'
import json
import sys
import time

running, pid, state, message, onboard_root, map_file, base_port, baudrate, command_mode, runtime_dir, log_dir = sys.argv[1:12]
payload = {
    "schema": "trashbot.o11.nav2_lifecycle.v1",
    "generated_at_ms": int(time.time() * 1000),
    "running": running == "true",
    "pid": int(pid) if pid.isdigit() else None,
    "state": state,
    "message": message,
    "onboard_root": onboard_root,
    "map_file": map_file,
    "base_port": base_port,
    "base_baudrate": int(baudrate) if baudrate.isdigit() else baudrate,
    "command_mode": command_mode,
    "launch": "ros2_trashbot_bringup autonomous.launch.py nav2_stack_only:=true",
    "runtime_dir": runtime_dir,
    "log_dir": log_dir,
    "vendor_sources": [
        "docs/vendor/VENDOR_INDEX.md",
        "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
        "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    ],
    "motion_requires_explicit_goal_execute": True,
    "sends_base_motion_commands": False,
    "robot_control_executed": False,
    "safe_to_control": False,
    "delivery_success": False,
    "blocked_commands_not_sent_by_start": ["/cmd_vel", "NavigateToPose goal", "/api/base/manual", "T=1", "T=11", "T=13"],
}
print(json.dumps(payload, ensure_ascii=False))
PY
}

write_status_file() {
  # status 文件是 PC/API 的现场复盘入口；写失败要让脚本失败。
  mkdir -p "$RUNTIME_DIR" "$LOG_DIR"
  json_status "$@" >"$STATUS_FILE"
}

emit_status_file_or_fallback() {
  # start/stop/status 都输出结构化 JSON，方便 PC 普通首屏显示根因。
  if [[ -s "$STATUS_FILE" ]]; then
    cat "$STATUS_FILE"
  else
    json_status "$@"
  fi
}

source_ros_setups() {
  # ROS2 setup 脚本可能引用未定义变量，source 阶段临时关闭 nounset。
  set +u
  source /opt/ros/humble/setup.bash
  source "$ONBOARD_ROOT/install/setup.bash"
  set -u
}

guard_runtime_inputs() {
  # Vendor 来源：WAVE ROVER 上/下位机用 115200 UART newline JSON；本车现场 base UART 为 /dev/ttyS5。
  case "$BASE_PORT" in
    /dev/ttyS5|/dev/serial/by-id/*|/dev/serial/by-path/*)
      ;;
    *)
      echo "refusing unexpected WAVE ROVER base UART: $BASE_PORT" >&2
      exit 40
      ;;
  esac
  case "$COMMAND_MODE" in
    ros|speed|pwm)
      ;;
    *)
      echo "unsupported command mode: $COMMAND_MODE" >&2
      exit 41
      ;;
  esac
}

require_runtime() {
  # start 前一次性确认 launch 所需的 ROS、安装空间、地图和串口都存在。
  test -f /opt/ros/humble/setup.bash
  test -f "$ONBOARD_ROOT/install/setup.bash"
  test -f "$MAP_FILE"
  test -e "$BASE_PORT"
  source_ros_setups
  command -v ros2 >/dev/null
}

pid_is_ours() {
  # 只承认本脚本 __run 子命令创建的 manager，stop 不按进程名扫杀其它 ROS2 任务。
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
  # pid 文件不存在时返回空字符串，status 仍输出结构化 stopped。
  if [[ -f "$PID_FILE" ]]; then
    tr -dc '0-9' <"$PID_FILE"
  fi
}

is_running() {
  local pid
  pid="$(current_pid)"
  [[ -n "$pid" ]] && pid_is_ours "$pid"
}

run_manager() {
  # manager 是独立进程组根；stop 只终止这个进程组和它启动的 launch。
  mkdir -p "$RUNTIME_DIR" "$LOG_DIR"
  echo "$$" >"$PID_FILE"
  write_status_file true "$$" "starting" "Nav2 lifecycle manager starting"
  guard_runtime_inputs
  require_runtime
  write_status_file true "$$" "running" "Nav2 stack-only launch running; wait for proof refresh to verify planner/controller"
  cd "$ONBOARD_ROOT"
  set +e
  ros2 launch ros2_trashbot_bringup autonomous.launch.py \
    nav2_stack_only:=true \
    map_file:="$MAP_FILE" \
    serial_port:="$BASE_PORT" \
    serial_baudrate:="$BASE_BAUDRATE" \
    command_mode:="$COMMAND_MODE" \
    >"$LAUNCH_LOG" 2>&1
  local launch_rc=$?
  set -e
  rm -f "$PID_FILE"
  if [[ "$launch_rc" -eq 0 ]]; then
    write_status_file false "" "stopped" "Nav2 stack-only launch exited cleanly"
  else
    write_status_file false "" "failed" "Nav2 stack-only launch exited with rc=$launch_rc; see $LAUNCH_LOG"
  fi
  return "$launch_rc"
}

start_manager() {
  # start 不复用用户 shell，避免 SSH 断开导致 ROS2 launch 被带走。
  if is_running; then
    emit_status_file_or_fallback true "$(current_pid)" "running" "Nav2 lifecycle already running"
    return 0
  fi
  mkdir -p "$RUNTIME_DIR" "$LOG_DIR"
  setsid bash "$SCRIPT_PATH" __run \
    --onboard-root "$ONBOARD_ROOT" \
    --map-file "$MAP_FILE" \
    --base-port "$BASE_PORT" \
    --base-baudrate "$BASE_BAUDRATE" \
    --command-mode "$COMMAND_MODE" \
    --runtime-dir "$RUNTIME_DIR" \
    >"$MANAGER_LOG" 2>&1 &
  local deadline=$((SECONDS + START_CONFIRM_TIMEOUT_S))
  while [[ "$SECONDS" -lt "$deadline" ]]; do
    if is_running; then
      emit_status_file_or_fallback true "$(current_pid)" "running" "Nav2 lifecycle manager running"
      return 0
    fi
    sleep 0.2
  done
  emit_status_file_or_fallback false "" "start_timeout" "Nav2 lifecycle manager did not confirm running"
  return 1
}

stop_manager() {
  # stop 只停本脚本 pid 文件指向的进程组，不清理其它 ros2/nav2 进程。
  local pid
  pid="$(current_pid)"
  if [[ -z "$pid" ]] || ! pid_is_ours "$pid"; then
    write_status_file false "" "stopped" "Nav2 lifecycle not running"
    emit_status_file_or_fallback false "" "stopped" "Nav2 lifecycle not running"
    return 0
  fi
  kill -TERM "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  for _ in {1..25}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 0.2
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
  write_status_file false "" "stopped" "Nav2 lifecycle stopped"
  emit_status_file_or_fallback false "" "stopped" "Nav2 lifecycle stopped"
}

case "$ACTION" in
  __run)
    run_manager
    ;;
  start)
    start_manager
    ;;
  stop)
    stop_manager
    ;;
  status)
    if is_running; then
      emit_status_file_or_fallback true "$(current_pid)" "running" "Nav2 lifecycle running"
    else
      rm -f "$PID_FILE"
      write_status_file false "" "stopped" "Nav2 lifecycle not running"
      emit_status_file_or_fallback false "" "stopped" "Nav2 lifecycle not running"
    fi
    ;;
  -h|--help|"")
    usage
    ;;
  *)
    echo "unsupported action: $ACTION" >&2
    usage >&2
    exit 2
    ;;
esac
