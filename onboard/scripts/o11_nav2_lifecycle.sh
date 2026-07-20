#!/usr/bin/env bash
# O11 Nav2 lifecycle：把 PC/API 的 start/stop 映射成受管 Nav2 runtime。
# 本脚本只启动 autonomous.launch.py 的 nav2_stack_only 模式，不启动巡逻或任务编排节点。
# 运动仍必须由显式确认后的 /api/nav2/goal/execute 触发；start 本身不发送 goal。
# 安全不变量：本入口只接受 base-disabled，不允许 auto 在现场意外打开底盘 UART。
# 安全不变量：legacy 模式必须 lidar=false/reuse=true，并要求 start 前已有 `/scan`。
# 安全不变量：sensor-owned 必须 lidar=true/reuse=false，两个布尔位不能同真或同假。
# 安全不变量：sensor-owned start 前 `/scan` publisher 必须为零，避免抢占其它雷达。
# 安全不变量：sensor-owned start 前 LiDAR port 必须无 holder，避免串口双开。
# 安全不变量：base UART 可以已有外部 holder，但本轮 pre/post 新增打开数必须为零。
# 安全不变量：LiDAR post 新 holder 必须全部属于本次 manager PGID 才能标记 owned。
# 安全不变量：publisher 只有在 pre=0、post>0 且 holder owned 时才能标记 owned。
# 安全不变量：manager PID 存活只是 launching，不等于传感器与 publisher 已就绪。
# 安全不变量：running 只能由 start_manager 完成 holder/publisher 后置验收后写入。
# 安全不变量：canonical map 路径固定，status 同时记录 YAML 与 image SHA-256。
# 安全不变量：map hash 只证明输入身份，不证明定位、路径或现场净空通过。
# 安全不变量：已有 O11 manager 时只回冲突，不覆盖其 status，也不自动 stop。
# 安全不变量：preflight 冲突不会创建 manager，因此不能借 cleanup 终止既有进程。
# 安全不变量：start timeout 保留 current owned PID，让 Upper 走唯一 scoped stop。
# 安全不变量：stop 只消费 PID_FILE，并再次核对 cmdline 属于本脚本 `__run`。
# 安全不变量：TERM/KILL 目标都是 owned process group，不按 ROS 节点名或进程名扫描。
# 安全不变量：脚本禁止按进程名批量终止，也不把其它 ROS2 runtime 当作可回收残留。
# 安全不变量：start/stop 都不发送 base stop，因为 Phase A 从未打开底盘控制面。
# 安全不变量：start 不发布 `/cmd_vel`，不调用 manual，也不发送任何 vendor motion JSON。
# 安全不变量：`physical_motion=false` 是 lifecycle 边界，不代表未来 goal 已获授权。
# 安全不变量：`safe_to_control=false` 与 `delivery_success=false` 在 status 中始终固定。
# 安全不变量：holder PID 只来自当前 fuser readback，不能从历史 artifact 推断。
# 安全不变量：publisher count 只来自当前 ROS2 graph 查询，topic 名存在不足以判绿。
# 安全不变量：任何 ROS CLI、设备或 package 缺口都必须结构化失败，不能静默降级。
# 安全不变量：状态 JSON 使用 Python 生成，避免 shell 转义破坏 PID、路径或中文原因。
# 安全不变量：本文件的 vendor 参数来源仍是 docs/vendor/VENDOR_INDEX.md 指向的本地材料。

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
BASE_ENABLED="${ROBER_NAV2_BASE_ENABLED:-auto}"
LIDAR_ENABLED="${ROBER_NAV2_LIDAR_ENABLED:-auto}"
REUSE_EXISTING_SCAN="${ROBER_NAV2_REUSE_EXISTING_SCAN:-auto}"
LIDAR_SERIAL_PORT="${ROBER_NAV2_LIDAR_SERIAL_PORT:-/dev/ttyACM0}"
LIDAR_SERIAL_BAUDRATE="${ROBER_NAV2_LIDAR_SERIAL_BAUDRATE:-230400}"
STATIC_LASER_TF_ENABLED="${ROBER_NAV2_STATIC_LASER_TF_ENABLED:-true}"
RUNTIME_DIR="${ROBER_NAV2_RUNTIME_DIR:-/tmp/rober_nav2_lifecycle}"
START_CONFIRM_TIMEOUT_S="${ROBER_NAV2_START_CONFIRM_TIMEOUT_S:-8}"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
NAV2_REQUIRED_PACKAGES=("nav2_bringup")
NAV2_PACKAGE_INSTALL_HINT="sudo apt-get install ros-humble-navigation2 ros-humble-nav2-bringup"
# 以下快照只由本次 start 填充；status JSON 通过前后差集证明串口/publisher 归属。
SENSOR_MODE="unresolved"
BASE_UART_PRE_HOLDER_PIDS=""
BASE_UART_POST_HOLDER_PIDS=""
LIDAR_SERIAL_PRE_HOLDER_PIDS=""
LIDAR_SERIAL_POST_HOLDER_PIDS=""
SCAN_PUBLISHER_PRE_COUNT="0"
SCAN_PUBLISHER_POST_COUNT="0"
LIDAR_HOLDER_OWNED="false"
SCAN_PUBLISHER_OWNED="false"
OWNER_PROCESS_GROUP_PID=""
BASE_UART_NEW_OPEN_PIDS_OBSERVED=""

usage() {
  cat <<'USAGE'
Usage: o11_nav2_lifecycle.sh start|stop|status [options]

Options:
  --onboard-root PATH     onboard workspace path, default /root/rober/onboard
  --map-file PATH         Nav2 map yaml, default /root/rober/onboard/runtime/maps/trashbot_map.yaml
  --base-port PATH        WAVE ROVER UART, default /dev/ttyS5
  --base-baudrate N       WAVE ROVER UART baudrate, default 115200
  --command-mode MODE     esp32_bridge command mode, default ros
  --base-enabled BOOL     true/false/auto; auto reuses an existing /esp32_bridge or UART holder
  --lidar-enabled BOOL    true/false/auto; auto reuses an existing /scan publisher or LiDAR holder
  --reuse-existing-scan BOOL  true/false/auto; true requires an external /scan publisher
  --lidar-serial-port PATH     LiDAR serial port, default /dev/ttyACM0
  --lidar-serial-baudrate N    LiDAR serial baudrate, default 230400
  --static-laser-tf-enabled BOOL  publish base_link->laser_frame TF, default true
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
    --base-enabled)
      BASE_ENABLED="$2"
      shift 2
      ;;
    --lidar-enabled)
      LIDAR_ENABLED="$2"
      shift 2
      ;;
    --reuse-existing-scan)
      REUSE_EXISTING_SCAN="$2"
      shift 2
      ;;
    --lidar-serial-port)
      LIDAR_SERIAL_PORT="$2"
      shift 2
      ;;
    --lidar-serial-baudrate)
      LIDAR_SERIAL_BAUDRATE="$2"
      shift 2
      ;;
    --static-laser-tf-enabled)
      STATIC_LASER_TF_ENABLED="$2"
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
  python3 - "$running" "$pid" "$state" "$message" "$ONBOARD_ROOT" "$MAP_FILE" "$BASE_PORT" "$BASE_BAUDRATE" "$COMMAND_MODE" "$BASE_ENABLED" "$LIDAR_ENABLED" "$LIDAR_SERIAL_PORT" "$LIDAR_SERIAL_BAUDRATE" "$STATIC_LASER_TF_ENABLED" "$RUNTIME_DIR" "$LOG_DIR" "$REUSE_EXISTING_SCAN" "$SENSOR_MODE" "$BASE_UART_PRE_HOLDER_PIDS" "$BASE_UART_POST_HOLDER_PIDS" "$LIDAR_SERIAL_PRE_HOLDER_PIDS" "$LIDAR_SERIAL_POST_HOLDER_PIDS" "$SCAN_PUBLISHER_PRE_COUNT" "$SCAN_PUBLISHER_POST_COUNT" "$LIDAR_HOLDER_OWNED" "$SCAN_PUBLISHER_OWNED" "$OWNER_PROCESS_GROUP_PID" "$BASE_UART_NEW_OPEN_PIDS_OBSERVED" <<'PY'
import hashlib
import json
import sys
import time
from pathlib import Path

(
    running, pid, state, message, onboard_root, map_file, base_port, baudrate,
    command_mode, base_enabled, lidar_enabled, lidar_port, lidar_baudrate,
    static_laser_tf_enabled, runtime_dir, log_dir,
    reuse_existing_scan, sensor_mode, base_pre_text, base_post_text,
    lidar_pre_text, lidar_post_text, scan_pre_text, scan_post_text,
    lidar_holder_owned_text, scan_publisher_owned_text, owner_process_group_pid,
    base_uart_new_open_pids_observed_text,
) = sys.argv[1:29]

# PID 列表来自 fuser，只保留正整数；差集是本轮 new-open 的唯一计数来源。
def pid_list(raw):
    return sorted({int(item) for item in raw.replace(",", " ").split() if item.isdigit()})

base_pre = pid_list(base_pre_text)
base_post = pid_list(base_post_text)
base_new_observed = pid_list(base_uart_new_open_pids_observed_text)
lidar_pre = pid_list(lidar_pre_text)
lidar_post = pid_list(lidar_post_text)
map_path = Path(map_file)
map_sha256 = hashlib.sha256(map_path.read_bytes()).hexdigest() if map_path.is_file() else None
# canonical YAML 的 image 行只做本地相对路径解析；不加载 YAML 以减少板端依赖。
image_path = None
image_sha256 = None
if map_path.is_file():
    for raw_line in map_path.read_text(encoding="utf-8").splitlines():
        if raw_line.strip().startswith("image:"):
            image_value = raw_line.split(":", 1)[1].strip().strip("'\"")
            candidate = Path(image_value)
            image_path = candidate if candidate.is_absolute() else map_path.parent / candidate
            break
if image_path is not None and image_path.is_file():
    image_sha256 = hashlib.sha256(image_path.read_bytes()).hexdigest()
payload = {
    "schema": "trashbot.o11.nav2_lifecycle.v1",
    "generated_at_ms": int(time.time() * 1000),
    "running": running == "true",
    "pid": int(pid) if pid.isdigit() else None,
    "state": state,
    "message": message,
    # 只有当前响应携带 manager PID 才表示本次 start 可能创建了需要回收的 owned process group。
    "start_owned_process_created": bool(pid.isdigit() and state in {"starting", "launching", "running", "start_timeout"}),
    "onboard_root": onboard_root,
    "map_file": map_file,
    "base_port": base_port,
    "base_baudrate": int(baudrate) if baudrate.isdigit() else baudrate,
    "command_mode": command_mode,
    "base_enabled": base_enabled,
    "lidar_enabled": lidar_enabled,
    "reuse_existing_scan": reuse_existing_scan,
    "sensor_mode": sensor_mode,
    "lidar_serial_port": lidar_port,
    "lidar_serial_baudrate": int(lidar_baudrate) if lidar_baudrate.isdigit() else lidar_baudrate,
    "static_laser_tf_enabled": static_laser_tf_enabled,
    "map_identity": {
        "path": map_file,
        "canonical_path": "/root/rober/onboard/runtime/maps/trashbot_map.yaml",
        "canonical_path_match": map_file == "/root/rober/onboard/runtime/maps/trashbot_map.yaml",
        "yaml_sha256": map_sha256,
        "image_path": str(image_path) if image_path is not None else None,
        "image_sha256": image_sha256,
    },
    "base_uart_pre_holder_pids": base_pre,
    "base_uart_post_holder_pids": base_post,
    # count 使用本轮轮询期间见过的并集，避免短暂打开后关闭被最终 post 快照洗掉。
    "base_uart_new_open_pids_observed": base_new_observed,
    "base_uart_new_open_count": len(base_new_observed),
    "lidar_serial_pre_holder_pids": lidar_pre,
    "lidar_serial_post_holder_pids": lidar_post,
    "lidar_serial_new_open_count": len(set(lidar_post) - set(lidar_pre)),
    "scan_publisher_pre_count": int(scan_pre_text) if scan_pre_text.isdigit() else 0,
    "scan_publisher_post_count": int(scan_post_text) if scan_post_text.isdigit() else 0,
    "lidar_holder_owned": lidar_holder_owned_text == "true",
    "scan_publisher_owned": scan_publisher_owned_text == "true",
    "owner_process_group_pid": int(owner_process_group_pid) if owner_process_group_pid.isdigit() else None,
    "sensor_ownership": {
        "mode": sensor_mode,
        "lidar_serial": "owned_process_group" if lidar_holder_owned_text == "true" else "external_or_unproven",
        "scan_publisher": "owned_process_group" if scan_publisher_owned_text == "true" else "external_or_unproven",
    },
    "launch": "ros2_trashbot_bringup autonomous.launch.py nav2_stack_only:=true",
    "runtime_dir": runtime_dir,
    "log_dir": log_dir,
    "vendor_sources": [
        "docs/vendor/VENDOR_INDEX.md",
        "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
        "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    ],
    "motion_requires_explicit_goal_execute": True,
    "physical_motion": False,
    "broad_kill_used": False,
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

normalize_bool_or_auto() {
  # launch 只接受 true/false，脚本入口额外支持 auto 用于避免现场串口重复占用。
  case "${1,,}" in
    true|false|auto)
      echo "${1,,}"
      ;;
    *)
      echo "invalid boolean/auto value: $1" >&2
      exit 43
      ;;
  esac
}

ros_node_exists() {
  local node_name="$1"
  ros2 node list 2>/dev/null | grep -Fx "$node_name" >/dev/null 2>&1
}

scan_has_publisher() {
  # 只读检查 /scan 是否已有发布者；已有雷达 runtime 时不再抢 LiDAR 串口。
  ros2 topic info /scan 2>/dev/null | grep -E "Publisher count:[[:space:]]*[1-9]" >/dev/null 2>&1
}

port_has_holder() {
  local port="$1"
  [[ -e "$port" ]] && fuser "$port" >/dev/null 2>&1
}

resolve_runtime_auto_flags() {
  BASE_ENABLED="$(normalize_bool_or_auto "$BASE_ENABLED")"
  LIDAR_ENABLED="$(normalize_bool_or_auto "$LIDAR_ENABLED")"
  REUSE_EXISTING_SCAN="$(normalize_bool_or_auto "$REUSE_EXISTING_SCAN")"
  STATIC_LASER_TF_ENABLED="$(normalize_bool_or_auto "$STATIC_LASER_TF_ENABLED")"
  if [[ "$BASE_ENABLED" == "auto" ]]; then
    if ros_node_exists "/esp32_bridge" || port_has_holder "$BASE_PORT"; then
      BASE_ENABLED="false"
    else
      BASE_ENABLED="true"
    fi
  fi
  if [[ "$LIDAR_ENABLED" == "auto" ]]; then
    if scan_has_publisher || port_has_holder "$LIDAR_SERIAL_PORT"; then
      LIDAR_ENABLED="false"
    else
      LIDAR_ENABLED="true"
    fi
  fi
  if [[ "$REUSE_EXISTING_SCAN" == "auto" ]]; then
    REUSE_EXISTING_SCAN="$([[ "$LIDAR_ENABLED" == "false" ]] && echo true || echo false)"
  fi
  if [[ "$STATIC_LASER_TF_ENABLED" == "auto" ]]; then
    STATIC_LASER_TF_ENABLED="true"
  fi
}

port_holder_pids() {
  # fuser 只读设备 holder；设备不存在或无人持有时返回空列表而不是失败。
  local port="$1"
  [[ -e "$port" ]] || return 0
  { fuser "$port" 2>/dev/null || true; } | tr ' ' '\n' | tr -dc '0-9\n' | sed '/^$/d' | sort -n -u | tr '\n' ' '
}

scan_publisher_count() {
  # 解析 ROS2 标准 Publisher count；CLI 不可用或 topic 不存在时安全回落为 0。
  local count
  count="$({ ros2 topic info /scan 2>/dev/null || true; } | sed -n 's/^[[:space:]]*Publisher count:[[:space:]]*//p' | head -n 1)"
  [[ "$count" =~ ^[0-9]+$ ]] && echo "$count" || echo 0
}

new_holder_pids() {
  # 只输出 post 中不在 pre 的 PID，不能把现场既有 holder 记到本轮 ownership。
  local pre=" $1 "
  local pid
  for pid in $2; do
    [[ "$pre" == *" $pid "* ]] || echo "$pid"
  done
}

record_base_uart_new_holders() {
  # base-disabled 合同对瞬时新 holder 也必须 sticky fail closed，不能只看最后一次 post 快照。
  # observed 加边界空格后按完整 PID 比较，避免 PID 12 与 112 发生子串误判。
  local observed=" $BASE_UART_NEW_OPEN_PIDS_OBSERVED "
  local pid
  for pid in $(new_holder_pids "$BASE_UART_PRE_HOLDER_PIDS" "$BASE_UART_POST_HOLDER_PIDS"); do
    # 已见 PID 不重复追加，status 中的计数表示唯一 holder 数而不是轮询次数。
    [[ "$observed" == *" $pid "* ]] || BASE_UART_NEW_OPEN_PIDS_OBSERVED+=" $pid"
  done
  # 追加时只会产生一个前导空格，用参数展开去掉，避免为证据归一化引入 xargs 依赖。
  BASE_UART_NEW_OPEN_PIDS_OBSERVED="${BASE_UART_NEW_OPEN_PIDS_OBSERVED# }"
}

new_lidar_holders_are_owned() {
  # 新 holder 必须全部位于 O11 manager 的进程组；任一越界都 fail closed。
  local owner_pid="$1"
  local new_pids
  new_pids="$(new_holder_pids "$LIDAR_SERIAL_PRE_HOLDER_PIDS" "$LIDAR_SERIAL_POST_HOLDER_PIDS")"
  [[ -n "$new_pids" ]] || return 1
  local pid pgid
  for pid in $new_pids; do
    pgid="$({ ps -o pgid= -p "$pid" 2>/dev/null || true; } | tr -dc '0-9')"
    [[ "$pgid" == "$owner_pid" ]] || return 1
  done
}

guard_sensor_contract() {
  # O11 安全入口只接受 base-disabled 的 legacy reuse 或 sensor-owned 两个互斥模式。
  if [[ "$MAP_FILE" != "/root/rober/onboard/runtime/maps/trashbot_map.yaml" ]]; then
    write_status_file false "" "failed_noncanonical_map" "O11 strict lifecycle requires the canonical map"
    return 1
  fi
  if [[ "$BASE_ENABLED" != "false" ]]; then
    write_status_file false "" "failed_unsafe_base_mode" "base_enabled must be false for O11 no-motion lifecycle"
    return 1
  fi
  if [[ "$LIDAR_ENABLED" == "true" && "$REUSE_EXISTING_SCAN" == "false" ]]; then
    SENSOR_MODE="sensor_owned_scan"
    # sensor-owned 不抢占现场已有 publisher/holder；冲突只报告，不清理对方。
    [[ "$SCAN_PUBLISHER_PRE_COUNT" == "0" ]] || {
      write_status_file false "" "failed_scan_publisher_conflict" "existing /scan publisher blocks sensor-owned start"
      return 1
    }
    [[ -z "$LIDAR_SERIAL_PRE_HOLDER_PIDS" ]] || {
      write_status_file false "" "failed_lidar_holder_conflict" "existing LiDAR holder blocks sensor-owned start"
      return 1
    }
    return 0
  fi
  if [[ "$LIDAR_ENABLED" == "false" && "$REUSE_EXISTING_SCAN" == "true" ]]; then
    SENSOR_MODE="legacy_existing_scan"
    [[ "$SCAN_PUBLISHER_PRE_COUNT" -ge 1 ]] || {
      write_status_file false "" "failed_existing_scan_missing" "legacy reuse requires an existing /scan publisher"
      return 1
    }
    return 0
  fi
  write_status_file false "" "failed_invalid_sensor_mode" "invalid lidar_enabled/reuse_existing_scan combination"
  return 1
}

nav2_missing_packages() {
  # 先查 launch 直接依赖，避免 package 缺失时只在长日志里留下晦涩失败。
  local package
  local missing=()
  for package in "${NAV2_REQUIRED_PACKAGES[@]}"; do
    if ! ros2 pkg prefix "$package" >/dev/null 2>&1; then
      missing+=("$package")
    fi
  done
  local IFS=","
  echo "${missing[*]}"
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
  case "$LIDAR_SERIAL_PORT" in
    /dev/ttyACM0|/dev/serial/by-id/*|/dev/serial/by-path/*)
      ;;
    *)
      echo "refusing unexpected LiDAR serial port: $LIDAR_SERIAL_PORT" >&2
      exit 44
      ;;
  esac
}

require_runtime() {
  # start 前一次性确认 launch 所需的 ROS、安装空间、地图和串口都存在。
  test -f /opt/ros/humble/setup.bash
  test -f "$ONBOARD_ROOT/install/setup.bash"
  test -f "$MAP_FILE"
  source_ros_setups
  resolve_runtime_auto_flags
  if [[ "$BASE_ENABLED" == "true" ]]; then
    test -e "$BASE_PORT"
  fi
  if [[ "$LIDAR_ENABLED" == "true" ]]; then
    test -e "$LIDAR_SERIAL_PORT"
  fi
  command -v ros2 >/dev/null
  local missing_packages
  missing_packages="$(nav2_missing_packages)"
  if [[ -n "$missing_packages" ]]; then
    local message
    message="Missing ROS package(s): $missing_packages; install with: $NAV2_PACKAGE_INSTALL_HINT"
    write_status_file false "" "failed_missing_dependency" "$message"
    echo "$message" >&2
    exit 42
  fi
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
  # manager 存活不等于 LiDAR/publisher 已就绪；running 只能由 start_manager 后置验收写入。
  write_status_file true "$$" "launching" "Nav2 stack-only launch starting; sensor ownership not yet confirmed"
  cd "$ONBOARD_ROOT"
  set +e
  ros2 launch ros2_trashbot_bringup autonomous.launch.py \
    nav2_stack_only:=true \
    map_file:="$MAP_FILE" \
    base_enabled:="$BASE_ENABLED" \
    serial_port:="$BASE_PORT" \
    serial_baudrate:="$BASE_BAUDRATE" \
    command_mode:="$COMMAND_MODE" \
    lidar_enabled:="$LIDAR_ENABLED" \
    lidar_serial_port:="$LIDAR_SERIAL_PORT" \
    lidar_serial_baudrate:="$LIDAR_SERIAL_BAUDRATE" \
    static_laser_tf_enabled:="$STATIC_LASER_TF_ENABLED" \
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
    # 已有 manager 即 ownership 冲突；本请求不得复用、覆盖或 stop 对方。
    # 不能覆盖既有 owner 的 status 文件；直接输出本次未创建进程的冲突响应。
    json_status false "" "failed_owned_runtime_conflict" "Nav2 lifecycle manager already running"
    return 1
  fi
  mkdir -p "$RUNTIME_DIR" "$LOG_DIR"
  guard_runtime_inputs
  require_runtime
  # 启动前快照只读采集；base UART 可有既有 holder，但本轮新增必须保持为零。
  BASE_UART_PRE_HOLDER_PIDS="$(port_holder_pids "$BASE_PORT")"
  LIDAR_SERIAL_PRE_HOLDER_PIDS="$(port_holder_pids "$LIDAR_SERIAL_PORT")"
  SCAN_PUBLISHER_PRE_COUNT="$(scan_publisher_count)"
  if ! guard_sensor_contract; then
    emit_status_file_or_fallback false "" "failed_sensor_contract" "Nav2 sensor contract rejected"
    return 1
  fi
  setsid bash "$SCRIPT_PATH" __run \
    --onboard-root "$ONBOARD_ROOT" \
    --map-file "$MAP_FILE" \
    --base-port "$BASE_PORT" \
    --base-baudrate "$BASE_BAUDRATE" \
    --command-mode "$COMMAND_MODE" \
    --base-enabled "$BASE_ENABLED" \
    --lidar-enabled "$LIDAR_ENABLED" \
    --reuse-existing-scan "$REUSE_EXISTING_SCAN" \
    --lidar-serial-port "$LIDAR_SERIAL_PORT" \
    --lidar-serial-baudrate "$LIDAR_SERIAL_BAUDRATE" \
    --static-laser-tf-enabled "$STATIC_LASER_TF_ENABLED" \
    --runtime-dir "$RUNTIME_DIR" \
    >"$MANAGER_LOG" 2>&1 &
  local deadline=$((SECONDS + START_CONFIRM_TIMEOUT_S))
  while [[ "$SECONDS" -lt "$deadline" ]]; do
    if is_running; then
      OWNER_PROCESS_GROUP_PID="$(current_pid)"
      BASE_UART_POST_HOLDER_PIDS="$(port_holder_pids "$BASE_PORT")"
      record_base_uart_new_holders
      LIDAR_SERIAL_POST_HOLDER_PIDS="$(port_holder_pids "$LIDAR_SERIAL_PORT")"
      SCAN_PUBLISHER_POST_COUNT="$(scan_publisher_count)"
      if [[ "$SENSOR_MODE" == "sensor_owned_scan" ]]; then
        if new_lidar_holders_are_owned "$OWNER_PROCESS_GROUP_PID"; then
          LIDAR_HOLDER_OWNED="true"
        fi
        if [[ "$SCAN_PUBLISHER_PRE_COUNT" == "0" && "$SCAN_PUBLISHER_POST_COUNT" -ge 1 && "$LIDAR_HOLDER_OWNED" == "true" ]]; then
          SCAN_PUBLISHER_OWNED="true"
        fi
        if [[ -z "$BASE_UART_NEW_OPEN_PIDS_OBSERVED" && "$LIDAR_HOLDER_OWNED" == "true" && "$SCAN_PUBLISHER_OWNED" == "true" ]]; then
          write_status_file true "$OWNER_PROCESS_GROUP_PID" "running" "Nav2 sensor-owned lifecycle running"
          emit_status_file_or_fallback true "$OWNER_PROCESS_GROUP_PID" "running" "Nav2 sensor-owned lifecycle running"
          return 0
        fi
      elif [[ -z "$BASE_UART_NEW_OPEN_PIDS_OBSERVED" && "$SCAN_PUBLISHER_POST_COUNT" -ge 1 ]]; then
        # legacy 模式明确把 holder/publisher 标成 external，不能冒充本进程组所有权。
        write_status_file true "$OWNER_PROCESS_GROUP_PID" "running" "Nav2 legacy lifecycle reusing external /scan"
        emit_status_file_or_fallback true "$OWNER_PROCESS_GROUP_PID" "running" "Nav2 legacy lifecycle reusing external /scan"
        return 0
      fi
    fi
    sleep 0.2
  done
  # timeout 时保留 owned manager，Upper semantic failure 随即调用唯一 o11 stop 做 scoped cleanup。
  write_status_file true "$(current_pid)" "start_timeout" "Nav2 lifecycle sensor ownership did not confirm running"
  emit_status_file_or_fallback true "$(current_pid)" "start_timeout" "Nav2 lifecycle sensor ownership did not confirm running"
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
