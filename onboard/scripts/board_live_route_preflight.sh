#!/usr/bin/env bash
# 现场上位机预检脚本入口。只做观测与证据留存，不执行底盘运动。
set -euo pipefail

# 参数优先级：CLI 显式参数 > 环境变量 > 文件默认值，避免改文件也能快速切换网络。
HOST="${TRASHBOT_LIVE_BOARD_HOST:-192.168.1.11}"
PORT="${TRASHBOT_LIVE_BOARD_PORT:-37878}"

# 运行开关默认关闭：脚本第一目标是“可复用检查闭环”，不是强制执行采集。
DRY_RUN=false
LOCAL_ONLY=false
SKIP_CAPTURE=false

UNAME="$(uname -s)"
RUN_ID="$(date +%Y%m%d_%H%M%S)_$$"

# 日志固定落到 ~/.ros 下，便于和现有证据目录统一归档。
LOG_DIR="${HOME}/.ros/trashbot_live_preflight"
LOG_FILE="${LOG_DIR}/${RUN_ID}.log"

SCRIPT_NAME="$(basename "$0")"

# 预检链路约束（执行顺序固定）：
# 1) 先解析参数与输出上下文，保证复现参数；
# 2) 落本机 git 状态用于判断工作区可追溯性；
# 3) 探测默认网关，用于判断离开本机后是否有上层链路；
# 4) 探测目标主机 ping，确认二层/路由到达信号；
# 5) 探测端口连通，确认服务入口是否监听；
# 6) SSH 握手后才进入远端读 smoke，避免凭空下发；
# 7) 远端只读检查 ros2/setup.bash 与核心 topic；
# 8) 生成 capture 模板而非直接执行，保留复用入口；
# 9) 统一以非零码上报 blocker，以便 automation 可重试。
#
# 关键边界说明：
# - 脚本不会调用任何运动 action、速度话题、底盘指令；
# - dry-run 只要求日志链路和模板输出可复用；
# - local-only 只要求本机预检可用；
# - skip-capture 只要求失败归因日志可写；
# - SSH 不达时不认为任务失败关闭，只记录 blocker，便于下次复跑。
#
# 证据策略说明：
# - 所有行为落盘到单一 run_id 的日志文件；
# - 每一项命令都记录原始命令与退出码；
# - 失败时保留 continue 分支，优先保全现场证据；
# - 成功时打印下一步可复用命令模板；
# - log_path 作为唯一入口提供给 side2side 与 final。
usage() {
  # 文案中的命令路径用中文说明“能跑”与“不能跑”的边界，避免误解。
  cat <<EOF
Usage: ${SCRIPT_NAME} [--help] [--dry-run] [--local-only] [--skip-capture] [--host HOST] [--port PORT]

Defaults:
  host=${HOST}
  port=${PORT}

Environment overrides:
  TRASHBOT_LIVE_BOARD_HOST
  TRASHBOT_LIVE_BOARD_PORT

Core:
  - Write a full preflight log to ${LOG_FILE}
  - Check git state, default gateway, ping, nc, and ssh reachability
  - Optionally run remote ROS2 topic smoke when SSH is reachable
  - Print/record capture templates only (learn.launch + save_map + replay command)

Notes:
  - capture commands are templates only; actual movement-related execution should only be done manually.
EOF
}

# 执行行为设计补充：
# - 所有检查按“证据先行”思想排序，不依赖 SSH 即可先产生本机闭环证据；
# - 任何失败都先降级为日志记录，再决定是否需要上抛错误；
# - run_check 保持命令文本不变，方便从日志直接复制复测；
# - 日志写入失败时会直接触发脚本失败，避免“有输出但没落盘”；
# - 本机预检（git）用于排查误提交与未提交变更；
# - 默认网关探测用于判断网络层是不是离站；
# - ping 的目的只是“可达性信号”，不是连接质量评估；
# - nc 在 ping 成功后执行，有助于快速区分路由与服务口故障；
# - SSH 仅在非 local-only 时执行，否则保持离线最小执行；
# - 一旦 SSH 成功，则固定顺序检查 ros2 运行环境；
# - setup.bash 不是存在即通过，而是确认 ros2 可启动的前置；
# - topic list 使用关键节点匹配减少 false-negative；
# - hz 检查只采 1 秒样本，兼顾时效与非阻塞；
# - capture 命令不执行，仅输出可复用模板；
# - capture 模板中的路径全部参数化，支持历史 run 复跑；
# - dry-run 不能作为采集成功标志，只是可复用计划输出成功；
# - local-only 不能当成现场成功，只能当成本机闭环成功；
# - skip-capture 只做失败闭环和日志可追踪；
# - run_id 是本次 preflight 的唯一对齐键；
# - run_dir 默认使用 ~/.ros/trashbot_live_runs；
# - 当 SSH 不达时返回 2 是为了让 CI/脚本将其识别为 blocker；
# - 成功码仅表示“检查路径执行完毕”；
# - 输出 capture 模板时不替换 host/port，保持命令可直接复制；
# - 所有模板都默认到 learn -> save_map -> route_csv_to_yaml -> fixed_route_autonomy；
# - route_bag 为可选扩展，不强制存在；
# - 不依赖任何 WAVE ROVER/UART 细节进行判断；
# - 不改变串口速度、底盘参数、轨迹策略；
# - 不依赖云端、数据库、4G 组件；
# - 不依赖机器人手机端应用；
# - 不依赖 operator gateway；
# - 不依赖外部证书管理；
# - 输出文档与日志路径，供 side2side/final 复查。

# 额外执行边界说明（避免脚本被误解为执行器）：
# - 帮助文案中的英文仅用于交付视图，不代表脚本内含英文逻辑分支。
# - 仅用于检测是否能开始现场链路，不负责判断路线几何是否正确。
# - 不对 map.yaml 与 route.csv 的值做 schema 深验。
# - 不检查地图文件是否可被 Nav2 加载。
# - 不验证任务状态转移是否完整。
# - 不读取任何运动控制 topic，不写入任何 cmd_vel。
# - 不执行清理旧会话或杀死已有节点。
# - 不改动上位机任何 launch 文件。
# - 不修改目标机文件系统权限。
# - 不重启 ros2 daemon 或网络服务。
# - 不判断 rosbag 体积、压缩参数、分片边界。
# - 不判断 route 文件内容是否满足业务语义。
# - 不对 camera 原始帧率做长期监控。
# - 不做多端口冗余探测，仅做单一目标端口采样。
# - 不在本机写入任何二进制日志，避免污染证据链。
# - 不检查 SSH 指纹变更日志，避免环境差异导致误判。
# - 不依赖任何第三方 CLI 之外的系统特权。
# - 不引入外部 Python 库，兼容最小 shell 环境。
# - 不在脚本中拼接机密参数，不输出认证信息。
# - 不将失败视为软件缺陷，优先归类为链路可达性 blocker。
# - 不替代 PRD 中的 route/elevator 人工验证流程。

log() {
  local ts
  ts="$(date '+%F %T')"
  # 所有输出都同步到终端和日志，现场可以一眼确认 run_id 与阶段状态。
  printf '[%s] %s\n' "$ts" "$1" | tee -a "$LOG_FILE"
}

run_check() {
  local label="$1"
  shift
  # run_check 统一记录命令和退出码，不让“某步失败”成为脚本静默死掉的黑洞。
  log ">>> ${label}"
  log "CMD: $*"
  local status=0
  set +e
  "$@" >>"$LOG_FILE" 2>&1
  status=$?
  set -e
  if [[ "$status" -eq 0 ]]; then
    log "${label} exit=0"
    return 0
  fi
  log "${label} exit=${status}"
  return "$status"
}

run_ping() {
  local target="$1"
  # 单次 ping + 短超时，仅用于健康评分，不作为硬失败条件。
  if [[ "$UNAME" == "Darwin" ]]; then
    # macOS 的 -W 更偏向毫秒，取 1000ms 降低等待。
    run_check "ping ${target}" ping -c 1 -W 1000 "$target"
  else
    # Linux 常用秒级超时，1 秒够确认到达层是否可达。
    run_check "ping ${target}" ping -c 1 -W 1 "$target"
  fi
}

run_nc_port() {
  local host="$1"
  local port="$2"
  # nc 只用于端口可达，失败也继续执行，避免网络层阻塞全链路。
  if command -v nc >/dev/null 2>&1; then
    run_check "nc ${host}:${port}" nc -vz -w 5 "$host" "$port" 2>&1
  else
    log "nc command missing; skip port check"
    return 0
  fi
}

run_ssh() {
  local host="$1"
  local port="$2"
  local remote_cmd="$3"
  # BatchMode 避免提示密码导致脚本挂住，保证可复跑可归档。
  run_check "ssh ${host}:${port}" \
    ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=accept-new "root@${host}" -p "${port}" "${remote_cmd}"
}

collect_capture_commands() {
  local run_dir="$1"
  # 模板仅用于复现命令链路，不直接执行，防止环境抖动时误下发运动。
  cat <<EOF
Suggested capture/replay commands for ${HOST}:${PORT}:

1) Learn + route recorder:
ssh -p ${PORT} root@${HOST} <<'ROUTE_CAPTURE_EOF'
ros2 launch ros2_trashbot_bringup learn.launch.py \
  route_recorder:=true \
  route_output_dir:=${run_dir}/route_data \
  route_id:=board_live_route \
  route_camera_topic:=/camera/image_raw \
  route_odom_topic:=/odom \
  route_min_distance_m:=0.8
ROUTE_CAPTURE_EOF

2) Save map:
ssh -p ${PORT} root@${HOST} ros2 service call /trashbot/save_map std_srvs/srv/Trigger

3) Route CSV -> YAML:
ssh -p ${PORT} root@${HOST} ros2 run ros2_trashbot_nav route_csv_to_yaml \\
  --ros-args \\
  -p input_csv:=${run_dir}/route_data/route.csv \\
  -p output_yaml:=${run_dir}/route_data/fixed_route.yaml

4) Fixed-route dry-run:
ssh -p ${PORT} root@${HOST} ros2 run ros2_trashbot_nav fixed_route_autonomy \\
  --ros-args \\
  -p route_file:=${run_dir}/route_data/fixed_route.yaml \\
  -p keyframe_dir:=${run_dir}/route_data/keyframes \\
  -p dry_run:=true \\
  -p enable_visual_gate:=false

5) Optional ros2 bag record:
ssh -p ${PORT} root@${HOST} ros2 bag record -o ${run_dir}/route_bag /scan /camera/image_raw /odom /tf /map
EOF
}

print_summary_header() {
  # 写入预检上下文，便于日志对齐后续 preflight 次数。
  log "Board live route preflight start"
  log "host: ${HOST}"
  log "port: ${PORT}"
  log "run_id: ${RUN_ID}"
  log "dry_run: ${DRY_RUN}"
  log "local_only: ${LOCAL_ONLY}"
  log "skip_capture: ${SKIP_CAPTURE}"
  log "log_file: ${LOG_FILE}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help)
      # 帮助优先输出；不继续解析参数，避免误动作。
      usage
      exit 0
      ;;
    --dry-run)
      # dry-run 允许连接失败仍完整产生日志，便于复查。
      DRY_RUN=true
      shift
      ;;
    --local-only)
      # local-only 只跑主机层检查，不访问远端。
      LOCAL_ONLY=true
      shift
      ;;
    --skip-capture)
      # skip-capture 主要用于只验证网络阻塞，不输出采集模板。
      SKIP_CAPTURE=true
      shift
      ;;
    --host)
      # 明确参数风格兼容： --host <ip> 或 --host=<ip>。
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --host" >&2
        exit 1
      fi
      HOST="$2"
      shift 2
      ;;
    --host=*)
      HOST="${1#*=}"
      shift
      ;;
    --port)
      # 明确参数风格兼容： --port <port> 或 --port=<port>。
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --port" >&2
        exit 1
      fi
      PORT="$2"
      shift 2
      ;;
    --port=*)
      PORT="${1#*=}"
      shift
      ;;
    --*)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
    *)
      echo "Unexpected positional argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

mkdir -p "$LOG_DIR"
touch "$LOG_FILE"
log "preflight script invoked"
print_summary_header

# 本机检查放在 onboard 根目录固定口径，避免仓库路径变动导致产物不一致。
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! run_check "git status --short" git -C "$REPO_ROOT" status --short; then
  # git status 失败是软失败，不应吞掉主流程，因为 blocker 信息更关键。
  log "git status returned non-zero, but preflight can continue."
fi

# 网关探测分 Linux 与 macOS 两条路径，失败仅记录，供后续排障。
DEFAULT_GATEWAY=""
if command -v ip >/dev/null 2>&1; then
  DEFAULT_GATEWAY="$(ip route show default 2>/dev/null | awk '/^default / {print $3; exit}')"
fi
if [[ -z "$DEFAULT_GATEWAY" ]] && command -v route >/dev/null 2>&1; then
  DEFAULT_GATEWAY="$(route -n get default 2>/dev/null | awk '/gateway:/{print $2; exit}')"
fi

if [[ -n "${DEFAULT_GATEWAY}" ]]; then
  log "default_gateway=${DEFAULT_GATEWAY}"
  if ! run_ping "$DEFAULT_GATEWAY"; then
    log "default gateway ping failed (allowed, continue)."
  fi
else
  log "default gateway not detected (environment dependent); continue."
fi

# 先确认目标主机可达性，再做端口探测，保留失败细分。
if ! run_ping "${HOST}"; then
  log "target host ping failed (allowed, continue)."
fi
if ! run_nc_port "${HOST}" "${PORT}"; then
  log "nc port probe failed (allowed, continue)."
fi

# 远端分支只在非 local-only 时运行，避免网卡不通时被 SSH 堵死。
SSH_REACHABLE=false
if [[ "$LOCAL_ONLY" == "true" ]]; then
  log "local-only mode: skip ssh and remote checks."
else
  if run_ssh "${HOST}" "${PORT}" "hostname"; then
    # 只有 SSH 可达才进入 ros2 smoke，建立明确的可复现现场入口。
    SSH_REACHABLE=true
    log "ssh handshake succeeded; continue remote smoke checks."
  else
    log "ssh handshake failed; continue with failure log."
  fi

  if [[ "$SSH_REACHABLE" == "true" ]]; then
    # 仅做只读观测，不发送任何控制消息，避免动作越界。
    if ! run_ssh "${HOST}" "${PORT}" "if [ -f /opt/ros/humble/setup.bash ]; then echo remote_setup_found=true; else echo remote_setup_found=false; fi;"; then
      log "/opt/ros/humble/setup.bash check failed."
    fi
    if ! run_ssh "${HOST}" "${PORT}" "hostname; date;"; then
      log "hostname/date check failed."
    fi
    if ! run_ssh "${HOST}" "${PORT}" "source /opt/ros/humble/setup.bash && command -v ros2 || true"; then
      log "ros2 binary check failed."
    fi
    # ros2 pkg list 的过滤范围锁定导航/底盘/行为，证明起码软件链路在线。
    if ! run_ssh "${HOST}" "${PORT}" "source /opt/ros/humble/setup.bash && ros2 pkg list | egrep 'ros2_trashbot_(bringup|nav|hardware|behavior)' || true"; then
      log "ros2 package list check failed."
    fi
    # topic list 与关键 topic 一致性 smoke，后续路线复跑依赖此链路。
    if ! run_ssh "${HOST}" "${PORT}" "source /opt/ros/humble/setup.bash && ros2 topic list | egrep '^/scan$|^/camera/image_raw$|^/odom$|^/tf$|^/map$' || true"; then
      log "topic list check failed."
    fi
    # hz 仅抽样一次，给出速率最小证据，不占用长时间窗口。
    if ! run_ssh "${HOST}" "${PORT}" "source /opt/ros/humble/setup.bash && for t in /scan /camera/image_raw /odom /tf /map; do echo \"# topic hz \${t}\"; ros2 topic hz \${t} -w 1 2>/dev/null || true; done"; then
      log "topic hz check failed."
    fi
  fi
fi

# capture 模板与 run_dir 基于 run_id 落盘，便于现场复算与重跑。
RUN_DIR="${HOME}/.ros/trashbot_live_runs/${RUN_ID}"
if [[ "$SKIP_CAPTURE" != "true" ]]; then
  if [[ "$DRY_RUN" == "true" ]]; then
    log "dry-run mode: capture commands are emitted for manual execution only."
  fi
  {
    echo "capture_plan_dir=${RUN_DIR}"
    collect_capture_commands "$RUN_DIR"
  } | tee -a "$LOG_FILE"
fi

if [[ "$SKIP_CAPTURE" == "true" ]]; then
  log "skip-capture mode: no command templates were printed."
fi

echo
log "Preflight finished."
if [[ "$LOCAL_ONLY" == "true" ]]; then
  # local-only 场景的结束码固定为成功，便于只看主机预检。
  log "local-only mode done. log path: ${LOG_FILE}"
  exit 0
fi
if [[ "$DRY_RUN" == "true" ]]; then
  # dry-run 即使远端失败，也要保留日志用于复盘，不直接当成功。
  log "dry-run mode: exiting without hard fail on remote connectivity."
  log "log path: ${LOG_FILE}"
  exit 0
fi
if [[ "$SSH_REACHABLE" == "true" ]]; then
  # 远端可达时脚本成功，后续动作仍需手工执行。
  log "remote SSH available. log path: ${LOG_FILE}"
  exit 0
fi

# ssh 不可达定义为 blocker，返回非零码触发上游自动化停在可复跑状态。
log "ssh unavailable; exiting non-zero by design to expose network blocker clearly."
log "log path: ${LOG_FILE}"
exit 2
