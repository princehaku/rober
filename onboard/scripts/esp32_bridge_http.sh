#!/usr/bin/env bash
set -euo pipefail

# 上位机开机后必须自动恢复 /cmd_vel -> esp32_bridge -> WAVE ROVER HTTP 链路。
# 这里不直接写底盘 UART，底盘命令仍由 ROS /cmd_vel 和 bridge 的短脉冲逻辑统一收口。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ONBOARD_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# FastDDS SHM 在 Orange Pi 上容易留下锁文件；PC WASD 热路径优先使用稳定的 UDP/DDS 行为。
export RMW_FASTRTPS_USE_SHM="${RMW_FASTRTPS_USE_SHM:-0}"
export HOME="${HOME:-/root}"
export USER="${USER:-root}"
export LOGNAME="${LOGNAME:-root}"
export ROS_HOME="${ROS_HOME:-/root/.ros}"
export ROS_LOG_DIR="${ROS_LOG_DIR:-${ROS_HOME}/log}"

source_ros_setups() {
  # ROS setup 可能读取未定义变量，source 阶段临时关闭 nounset。
  set +u
  source /opt/ros/humble/setup.bash
  source "${ONBOARD_ROOT}/install/setup.bash"
  set -u
}

cleanup_stale_bridge() {
  # systemd 接管前清理脱管 esp32_bridge，避免两个节点同时订阅 /cmd_vel 或抢 debug log。
  local pid
  for proc in /proc/[0-9]*; do
    pid="${proc##*/}"
    [[ "${pid}" == "$$" ]] && continue
    [[ -r "${proc}/cmdline" ]] || continue
    local cmdline
    # /proc 进程可能在遍历时消失；失败时跳过即可，不能让开机服务因此退出。
    cmdline="$(tr '\0' ' ' <"${proc}/cmdline" 2>/dev/null || true)"
    cmdline="${cmdline:0:1200}"
    if [[ "${cmdline}" == *"ros2_trashbot_hardware esp32_bridge"* || "${cmdline}" == *"/ros2_trashbot_hardware/esp32_bridge --ros-args"* ]]; then
      echo "cleanup stale esp32_bridge pid=${pid}: ${cmdline}" >&2
      kill "${pid}" 2>/dev/null || true
      for _ in 1 2 3 4 5; do
        kill -0 "${pid}" 2>/dev/null || break
        sleep 0.2
      done
      kill -0 "${pid}" 2>/dev/null && kill -9 "${pid}" 2>/dev/null || true
    fi
  done
}

mkdir -p "${ROS_LOG_DIR}" "${ONBOARD_ROOT}/runtime"
source_ros_setups
cleanup_stale_bridge

# 参数来自 2026-07-03/04 真实上位机验证；硬件口径以 docs/vendor/VENDOR_INDEX.md 指向的
# WAVE_ROVER_V0.9/json_cmd.h 与 ugv_config.h 为准：main_type=1,module_type=0，运动命令用 T=11 PWM164。
# PC 手控仍走 ROS /cmd_vel，bridge 再通过 ESP32 HTTP 控制 WAVE ROVER，避免 PC API 直接抢底盘串口。
exec ros2 run ros2_trashbot_hardware esp32_bridge --ros-args \
  -r __node:=esp32_bridge \
  -p serial_port:="${ROBER_BASE_SERIAL_PORT:-/dev/ttyS5}" \
  -p serial_baudrate:="${ROBER_BASE_BAUDRATE:-115200}" \
  -p command_mode:="${ROBER_BRIDGE_COMMAND_MODE:-pwm}" \
  -p track_width_m:="${ROBER_BRIDGE_TRACK_WIDTH_M:-0.172}" \
  -p max_wheel_speed_mps:="${ROBER_BRIDGE_MAX_WHEEL_SPEED_MPS:-1.3}" \
  -p pwm_min_abs:="${ROBER_BRIDGE_PWM_MIN_ABS:-164}" \
  -p pwm_max_abs:="${ROBER_BRIDGE_PWM_MAX_ABS:-164}" \
  -p main_type:="${ROBER_BRIDGE_MAIN_TYPE:-1}" \
  -p module_type:="${ROBER_BRIDGE_MODULE_TYPE:-0}" \
  -p command_transport:="${ROBER_BRIDGE_COMMAND_TRANSPORT:-http}" \
  -p wave_rover_http_base_url:="${ROBER_WAVE_ROVER_HTTP_BASE_URL:-http://192.168.1.3}" \
  -p http_timeout_s:="${ROBER_WAVE_ROVER_HTTP_TIMEOUT_S:-0.6}" \
  -p feedback_debug_log_path:="${ROBER_BRIDGE_FEEDBACK_DEBUG_LOG:-${ONBOARD_ROOT}/runtime/wave_rover_feedback_debug.jsonl}" \
  -p command_debug_log_path:="${ROBER_BRIDGE_COMMAND_DEBUG_LOG:-${ONBOARD_ROOT}/runtime/wave_rover_command_debug.jsonl}"
