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
# 串口默认只描述建议配置；status 必须通过 current evidence 才能确认实际 holder。
SERIAL_PORT="/dev/ttyACM0"
# 230400 来自本地 vendor reference，不能在 bare status 中直接输出为 current。
SERIAL_BAUDRATE="230400"
FRAME_ID="laser_frame"
# 三个 explicit 标记用于区分调用者 argv 与上面的静态默认值。
SERIAL_PORT_EXPLICIT="false"
SERIAL_BAUDRATE_EXPLICIT="false"
FRAME_ID_EXPLICIT="false"
# runtime 目录保存 PID、状态、日志和 diagnostics，但 status 分支只读取它们。
RUNTIME_DIR="${ROBER_LIDAR_RUNTIME_DIR:-/tmp/rober_lidar_lifecycle}"
# proc root 可在测试中隔离；真实板默认固定读取 Linux /proc。
PROC_ROOT="${ROBER_LIDAR_PROC_ROOT:-/proc}"
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
  --serial-baudrate N    LiDAR baudrate, default 230400
  --frame-id NAME        LiDAR frame id, default laser_frame
  --runtime-dir PATH     state/log root, default /tmp/rober_lidar_lifecycle
  -h, --help             show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  # 参数解析只记录显式性，不在此阶段判断 current；动作分支稍后按证据裁决。
  case "$1" in
    --onboard-root)
      ONBOARD_ROOT="$2"
      shift 2
      ;;
    --serial-port)
      SERIAL_PORT="$2"
      SERIAL_PORT_EXPLICIT="true"
      shift 2
      ;;
    --serial-baudrate)
      SERIAL_BAUDRATE="$2"
      SERIAL_BAUDRATE_EXPLICIT="true"
      shift 2
      ;;
    --frame-id)
      FRAME_ID="$2"
      FRAME_ID_EXPLICIT="true"
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
# logs 与 diagnostics 路径由 start/__run 写入；status 不创建或刷新这些 artifact。
LOG_DIR="$RUNTIME_DIR/logs"
MANAGER_LOG="$LOG_DIR/lidar_lifecycle_manager.log"
DRIVER_LOG="$LOG_DIR/lidar_driver.log"
TF_LOG="$LOG_DIR/tf_static.log"
DIAGNOSTICS_FILE="$RUNTIME_DIR/lidar_driver_diagnostics.json"
DRIVER_PID_FILE="$RUNTIME_DIR/lidar_driver.pid"
TF_PID_FILE="$RUNTIME_DIR/tf_static.pid"
START_CONFIRM_TIMEOUT_S="${ROBER_LIDAR_START_CONFIRM_TIMEOUT_S:-4}"

json_status() {
  # 状态 JSON 由 Python 生成，避免 shell 手写转义把路径里的特殊字符写坏。
  # bare status 的参数是 reference/default，不可直接冒充当前运行值；解析器必须寻找当前证据。
  local running="$1"
  local pid="$2"
  local state="$3"
  local message="$4"
  python3 - "$running" "$pid" "$state" "$message" "$SERIAL_PORT" "$SERIAL_BAUDRATE" "$FRAME_ID" \
    "$RUNTIME_DIR" "$LOG_DIR" "$ACTION" "$SERIAL_PORT_EXPLICIT" "$SERIAL_BAUDRATE_EXPLICIT" \
    "$FRAME_ID_EXPLICIT" "$PROC_ROOT" "$STATUS_FILE" "$DIAGNOSTICS_FILE" "$SCRIPT_PATH" <<'PY'
import json
import subprocess
import sys
import time
from pathlib import Path

(
    # 前四项描述 status 外壳，不参与 current 候选的可信度判断。
    running,
    pid,
    state,
    message,
    # command_* 是本次脚本 argv；bare status 下它们只能视为配置默认。
    command_serial_port,
    command_baudrate,
    command_frame_id,
    # runtime/log 路径只用于定位持久状态和 diagnostics，不触发任何写操作。
    runtime_dir,
    log_dir,
    action,
    # explicit 标记区分调用者显式输入和脚本静态默认，避免默认值伪装 readback。
    serial_port_explicit,
    baudrate_explicit,
    frame_id_explicit,
    # proc/status/diagnostics 三个输入均为只读 current evidence 来源。
    proc_root,
    status_file,
    diagnostics_file,
    script_path,
) = sys.argv[1:18]


def positive_baudrate(value):
    # 所有来源统一做正整数校验，坏 JSON 或非法字符串不能进入 current 字段。
    # bool 在 Python 中属于 int 子类，必须先排除，避免 true 被误解为 baudrate=1。
    if isinstance(value, bool) or value is None:
        return None
    try:
        # 字符串归一允许兼容 shell JSON 的历史数值形态，但不接受浮点截断。
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    # 上限只承担防御性过滤，不声明任何 vendor 支持范围。
    return parsed if 0 < parsed <= 4_000_000 else None


def read_json(path):
    # status 必须保持只读；读取失败只丢弃该候选，不影响结构化 fail-closed 输出。
    try:
        # UTF-8 是项目 artifact 契约；不尝试猜测其他编码以免掩盖文件损坏。
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    # 顶层非 object 无法携带 PID/provenance，因此不能作为候选。
    return payload if isinstance(payload, dict) else None


def flag_value(argv, flag):
    # 同时兼容 `--flag value` 与 `--flag=value`，避免依赖进程命令行的单一格式。
    for index, item in enumerate(argv):
        # 分离参数形态需要确认后继项存在，截断 argv 不得抛异常或产生假值。
        if item == flag and index + 1 < len(argv):
            return argv[index + 1]
        # 等号形态只切第一次，保留值中可能存在的其他等号。
        if item.startswith(f"{flag}="):
            return item.split("=", 1)[1]
    # 缺 flag 是证据缺失，不回退到脚本默认。
    return None


def holder_argv(current_pid):
    # Linux 真机优先读取 /proc 的 NUL 分隔 argv；ps 仅作为无 /proc 平台的测试/诊断回退。
    cmdline_path = Path(proc_root) / str(current_pid) / "cmdline"
    try:
        # 直接读取 bytes 才能保留 Linux cmdline 的 NUL 边界。
        raw = cmdline_path.read_bytes()
    except OSError:
        raw = b""
    if raw:
        # 单项坏字节只替换展示字符，不影响其他 flag 的精确提取。
        return [item.decode("utf-8", errors="replace") for item in raw.split(b"\0") if item]
    try:
        # macOS 单元测试没有 /proc；限定 1 秒防止 status 被 ps 回退拖死。
        completed = subprocess.run(
            ["ps", "-p", str(current_pid), "-o", "command="],
            check=False,
            capture_output=True,
            text=True,
            timeout=1,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    # ps 回退只用于缺 /proc 的环境；真机 provenance 仍会明确标为 ps_command_fallback。
    # shell-like split 不处理复杂 quoting，因此真机验收仍以 /proc 数组为准。
    return completed.stdout.strip().split() if completed.returncode == 0 else []


def add_candidate(candidates, source, value, status, *, serial_port=None, candidate_pid=None):
    # 每个候选都保留来源与信任状态，便于 API/operator 看到 stale 或冲突，而不是静默覆盖。
    parsed = positive_baudrate(value)
    # 非法或缺失值不加入数组，避免消费者把 null candidate 当成一次 readback。
    if parsed is None:
        return
    candidates.append(
        {
            # source 是稳定机器字段，现场报告可直接定位证据层。
            "source": source,
            "baudrate": parsed,
            # port/PID 与 baudrate 一起保留，避免跨设备或跨 manager 拼接证据。
            "serial_port": serial_port,
            "pid": candidate_pid,
            # trusted_current 只由明确状态推导，不能由 baudrate 数值本身推导。
            "trusted_current": status == "trusted_current_candidate",
            "status": status,
        }
    )


is_running = running == "true"
current_pid = int(pid) if pid.isdigit() else None
# candidates 按优先级追加；后续选择仍显式检查 source，避免依赖隐含顺序。
candidates = []
# holder 摘要始终存在，running=false 时也能说明没有读取进程 argv。
holder = {
    # status 先给保守默认，只有受管 __run argv 解析成功才提升为 loaded。
    "status": "not_running" if not is_running else "argv_unavailable",
    "pid": current_pid,
    # argv 用数组保留 flag 边界，报告层不需要重新切整段字符串。
    "argv": [],
    "serial_port": None,
    "baudrate": None,
}

# running holder 是最高优先级；只接受包含本脚本 __run 的实际进程命令行。
if is_running and current_pid is not None:
    argv = holder_argv(current_pid)
    script_name = Path(script_path).name
    # 同时匹配脚本名与 __run，排除碰巧含相同 PID 文件的无关进程。
    if script_name in " ".join(argv) and "__run" in argv:
        holder_port = flag_value(argv, "--serial-port")
        holder_baudrate = positive_baudrate(flag_value(argv, "--serial-baudrate"))
        holder = {
            # argv 可读但缺 baudrate 时必须标 missing，不能补静态 230400。
            "status": "loaded" if holder_baudrate is not None else "baudrate_missing",
            "pid": current_pid,
            "argv": argv,
            "serial_port": holder_port,
            "baudrate": holder_baudrate,
        }
        add_candidate(
            candidates,
            # source 名直接表达当前值来自 running holder 的显式 flag。
            "running_holder.argv.--serial-baudrate",
            holder_baudrate,
            "trusted_current_candidate",
            serial_port=holder_port,
            candidate_pid=current_pid,
        )
    else:
        # 保留不可归因 argv 便于诊断，但它不能创建 current 候选。
        holder["argv"] = argv
        holder["status"] = "argv_not_managed_holder" if argv else "argv_unavailable"

# persisted status 只有 PID 与当前 holder 一致时才是 current；PID 漂移必须显式标 stale。
persisted = read_json(status_file)
if persisted is not None:
    # 历史 v1 同时出现过 baudrate/serial_baudrate，读取时兼容但输出统一为 baudrate。
    persisted_pid = persisted.get("pid")
    persisted_baudrate = persisted.get("baudrate", persisted.get("serial_baudrate"))
    persisted_port = persisted.get("serial_port")
    # running、当前 PID、持久 PID 三项必须同时成立才可标 trusted。
    pid_matched = bool(is_running and current_pid is not None and persisted_pid == current_pid)
    add_candidate(
        candidates,
        # source 显式编码 PID 是否匹配，使旧状态不会悄悄被过滤而丢失诊断价值。
        "persisted_status.pid_matched.baudrate" if pid_matched else "persisted_status.pid_mismatch.baudrate",
        persisted_baudrate,
        "trusted_current_candidate" if pid_matched else "pid_mismatch_stale",
        serial_port=persisted_port,
        candidate_pid=persisted_pid if isinstance(persisted_pid, int) else None,
    )

# diagnostics 是 driver 自己写出的运行事实；支持 raw diagnostics 的 config/serial 两种历史形态。
diagnostics = read_json(diagnostics_file)
if diagnostics is not None:
    # API 包装后的 diagnostics 使用 serial；driver 原始 artifact 使用 config。
    diagnostics_serial = diagnostics.get("serial") if isinstance(diagnostics.get("serial"), dict) else {}
    diagnostics_config = diagnostics.get("config") if isinstance(diagnostics.get("config"), dict) else {}
    # 先取更接近 runtime readback 的 serial 形态。
    diagnostics_baudrate = diagnostics_serial.get("serial_baudrate", diagnostics_serial.get("baudrate"))
    diagnostics_source = "driver_diagnostics.serial.serial_baudrate"
    diagnostics_port = diagnostics_serial.get("serial_port")
    if positive_baudrate(diagnostics_baudrate) is None:
        # serial 缺失时兼容 raw driver config，不能把不存在的 serial 字段写成来源。
        diagnostics_baudrate = diagnostics_config.get("serial_baudrate", diagnostics_config.get("baudrate"))
        diagnostics_source = "driver_diagnostics.config.serial_baudrate"
        diagnostics_port = diagnostics_config.get("serial_port")
    add_candidate(
        candidates,
        diagnostics_source,
        diagnostics_baudrate,
        # lifecycle 不 running 时 diagnostics 可能只是退出后残留，只保留为非 current 候选。
        "trusted_current_candidate" if is_running else "diagnostics_without_running_holder",
        serial_port=diagnostics_port,
        candidate_pid=current_pid,
    )

# 只有 start/__run 的显式 argv 才代表当前命令；bare status 的默认 230400 永远不进入 current。
if action in {"start", "__run"} and baudrate_explicit == "true":
    add_candidate(
        candidates,
        # status 即使显式传 flag 也不可信，因为它不是启动当前 holder 的命令。
        "current_command.argv.--serial-baudrate",
        command_baudrate,
        "trusted_current_candidate",
        serial_port=command_serial_port if serial_port_explicit == "true" else None,
        candidate_pid=current_pid,
    )

trusted = [item for item in candidates if item["trusted_current"]]
# holder 单独查找，确保它可以裁决 persisted/diagnostics 的漂移冲突。
holder_candidate = next((item for item in trusted if item["source"].startswith("running_holder.")), None)
# 去重后判断是否存在多值冲突，同值多来源是交叉印证而不是冲突。
trusted_values = sorted({item["baudrate"] for item in trusted})
selected = None
# 所有分支从 unknown 开始，只有充分 current 证据才能提升。
readback_status = "unknown_no_current_readback"
conflicts = []
if holder_candidate is not None:
    # holder 冲突时仍以实际进程 argv 为 current，同时把所有不同值保留下来供现场复核。
    selected = holder_candidate
    conflicts = [item for item in trusted if item["baudrate"] != selected["baudrate"]]
    readback_status = "current_with_candidate_conflict" if conflicts else "current"
elif len(trusted_values) == 1 and trusted:
    # 无 holder 但所有可信来源同值时，按既定候选优先级选第一个并保留完整数组。
    selected = trusted[0]
    readback_status = "current"
elif len(trusted_values) > 1:
    # 没有 holder 可以裁决时，不任选一个候选，避免 stale status 与 diagnostics 冲突被误报为 current。
    conflicts = trusted
    readback_status = "current_evidence_conflict_fail_closed"

selected_baudrate = selected["baudrate"] if selected else None
# 端口跟随选中候选；候选未带端口时才保留命令默认用于兼容旧消费者。
selected_port = selected.get("serial_port") if selected else None
# 与 230400 不同只表示 current/reference 分层，不代表 current 错误。
reference_conflict = selected_baudrate is not None and selected_baudrate != 230400
if selected is not None and reference_conflict and readback_status == "current":
    # 没有 runtime 候选互相冲突时，仍显式说明 current 与 vendor reference 不同。
    readback_status = "current_with_reference_conflict"

payload = {
    # schema 保持 v1 以兼容 Upper API；新增字段均为 additive。
    "schema": "trashbot.o1.lidar_lifecycle.v1",
    "generated_at_ms": int(time.time() * 1000),
    # lifecycle 状态只由 PID/进程检查决定，不由 diagnostics 内容倒推。
    "running": is_running,
    "pid": current_pid,
    "state": state,
    "message": message,
    "serial_port": selected_port or command_serial_port,
    # baudrate 是 current-only 字段；证据不足时必须序列化为 JSON null。
    "baudrate": selected_baudrate,
    "baudrate_readback_source": selected["source"] if selected else "unknown",
    "baudrate_readback_status": readback_status,
    # candidates/conflicts 允许调用方审计选择过程，避免只看到最终数字。
    "baudrate_candidates": candidates,
    "baudrate_conflicts": conflicts,
    "holder": holder,
    # vendor reference 永远独立，不能因数值恰好相同就变成 current 来源。
    "vendor_reference_baudrate": 230400,
    "vendor_reference_status": "reference_only_not_current",
    "frame_id": command_frame_id,
    # 路径字段用于 API 找到 diagnostics，不代表 status 已验证目录新鲜度。
    "runtime_dir": runtime_dir,
    "log_dir": log_dir,
    "driver_diagnostics_path": f"{runtime_dir}/lidar_driver_diagnostics.json",
    # driver/static_tf 是组件说明，不表示 status 启动了任何 ROS2 进程。
    "driver": "ros2_trashbot_hardware lidar_driver",
    "static_tf": "base_link -> laser_frame",
    "vendor_readback_boundary": {
        # vendor 索引和具体源码共同固定 230400 reference 的本地资料来源。
        "vendor_index": "docs/vendor/VENDOR_INDEX.md",
        "wave_rover_lidar_reference": "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
        "wave_rover_reference_baudrate": 230400,
        "wave_rover_reference_classification": "reference_only_not_current",
        "historical_field_baudrate_candidate": 150000,
        # 150000 只有现场 readback 能提升为 current，不能写成 vendor 结论。
        "historical_field_baudrate_classification": "current_only_when_runtime_readback_observed",
        "dedicated_lidar_vendor_doc_present_in_local_tree": False,
    },
    # 以下安全字段全部固定 false；修正状态语义不扩大控制权限。
    "safe_to_control": False,
    # status 不发送 LiDAR 启停字节，更不会发送任何底盘运动命令。
    "sends_base_motion_commands": False,
    "calls_base_manual": False,
    # uses_base_uart/publishes_cmd_vel 双重固定 false，防止消费者误解 runtime 存活。
    "uses_base_uart": False,
    "publishes_cmd_vel": False,
    # current baudrate readback 只证明状态语义，不证明机器人执行过控制或路线。
    "robot_control_executed": False,
    "route_execution_success": False,
    # delivery/HIL 必须由独立现场验收产生，本脚本永远不能提升这两个字段。
    "delivery_success": False,
    "hil_pass": False,
    # 明列底盘 UART 和禁用命令，便于审计本脚本的 LiDAR-only 边界。
    "blocked_base_uart": "/dev/ttyS5",
    "blocked_commands_not_sent": ["T=1", "T=13", "T=130", "T=131", "/cmd_vel", "/api/base/manual"],
}
print(json.dumps(payload, ensure_ascii=False))
PY
}

write_status_file() {
  # status 文件用于 API/SSH 复盘；HTTP start/stop 仍以命令退出码为准。
  # 写入只发生在 start/stop/__run，bare status 不调用本函数，避免只读查询污染证据。
  mkdir -p "$RUNTIME_DIR" "$LOG_DIR"
  json_status "$@" >"$STATUS_FILE"
}

emit_status_file_or_fallback() {
  # start 需要把 manager 写下的失败原因原样带回 HTTP stdout，方便 PC 显示根因。
  # 文件缺失才现场生成；已有 manager 结果不能被调用进程默认值覆盖。
  if [[ -s "$STATUS_FILE" ]]; then
    cat "$STATUS_FILE"
  else
    json_status "$@"
  fi
}

status_file_state() {
  # 用 python 读 JSON，避免 shell 对中文 message 或路径字符做脆弱切分。
  # 这里仅供 start confirmation 使用，不参与 bare status 的 baudrate 选择。
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
  # status 分支不会调用该函数，所以只读查询不加载 ROS2 环境。
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
  # kill -0 先验证 PID 存活，避免复用后的 stale pid 文件被当作 lifecycle。
  local pid="$1"
  if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
    return 1
  fi
  if [[ -r "$PROC_ROOT/$pid/cmdline" ]]; then
    tr '\0' ' ' <"$PROC_ROOT/$pid/cmdline" | grep -F "$(basename "$SCRIPT_PATH") __run" >/dev/null
    return $?
  fi
  ps -p "$pid" -o command= 2>/dev/null | grep -F "$(basename "$SCRIPT_PATH") __run" >/dev/null
}

current_pid() {
  # pid 文件不存在时返回空字符串，status 仍要输出结构化 JSON。
  # 只保留数字可阻止损坏 pid 文件向 kill/ps 注入额外参数。
  if [[ -f "$PID_FILE" ]]; then
    tr -dc '0-9' <"$PID_FILE"
  fi
}

is_running() {
  # running 必须同时满足 pid 文件存在、进程存活和受管 __run 命令匹配。
  local pid
  pid="$(current_pid)"
  [[ -n "$pid" ]] && pid_is_ours "$pid"
}

require_runtime() {
  # start 进入后台 manager 后再检查 runtime，让 API 快速拿到明确失败日志。
  # 该检查只属于启动路径；status 永远不触碰串口或 ROS2 runtime。
  test -f /opt/ros/humble/setup.bash
  test -f "$ONBOARD_ROOT/install/setup.bash"
  test -e "$SERIAL_PORT"
  source_ros_setups
  command -v ros2 >/dev/null
}

cleanup_children() {
  # driver 先收到 SIGTERM，给它机会发送 LiDAR stop bytes 并关闭串口。
  # 清理只处理本 manager 记录的子 PID，不扫描系统同名进程。
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
  # manager 的显式 argv 会成为 persisted status 与 holder provenance 的共同来源。
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
    -p diagnostics_path:="$DIAGNOSTICS_FILE" \
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
  # start 的安全 guard 必须先于 runtime 检查，错误串口不能进入后台进程。
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
  # status 只判断现有 manager 并调用只读证据解析器，绝不 start/stop lifecycle。
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
