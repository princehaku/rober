#!/usr/bin/env bash
set -o pipefail

RUN_DIR="${RUN_DIR:-/tmp/rober_wave_rover_min_actuation_probe}"
SCRIPT_PATH="${SCRIPT_PATH:-/tmp/wave_rover_min_actuation_probe.py}"
SERIAL_PORT="/dev/ttyS5"
LIDAR_PORT="/dev/ttyACM0"
SERVICE_NAME="trashbot-upper-robot-api.service"
STOPPED_SERVICE="false"

mkdir -p "${RUN_DIR}"

# ROS setup 内部会读取未定义环境变量，source 完成后再打开 nounset。
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
set -u

cleanup() {
  # 清场第一步先通过 ROS stop service 停车，避免先杀 bridge 导致无法下发零速。
  timeout 5 ros2 service call /trashbot/stop std_srvs/srv/Trigger "{}" >"${RUN_DIR}/cleanup_stop_service.log" 2>&1 || true
  # 再杀本轮 probe 和 ROS driver child 进程，避免 wrapper PID 退出后 executable 仍占串口。
  pkill -f "wave_rover_min_actuation_probe.py" || true
  pkill -f "ros2_trashbot_hardware/lib/ros2_trashbot_hardware/esp32_bridge" || true
  pkill -f "ros2_trashbot_hardware/lib/ros2_trashbot_hardware/lidar_driver" || true
  pkill -f "ros2 run ros2_trashbot_hardware esp32_bridge" || true
  pkill -f "ros2 run ros2_trashbot_hardware lidar_driver" || true
  sleep 1
  if [ "${STOPPED_SERVICE}" = "true" ]; then
    # 本轮如果停过 upper API，必须恢复 service active，让远程控制面回到常驻状态。
    systemctl start "${SERVICE_NAME}" || true
  fi
  {
    echo "[final service]"
    systemctl is-active "${SERVICE_NAME}" || true
    systemctl status "${SERVICE_NAME}" --no-pager -l | sed -n '1,14p' || true
    echo "[final lsof]"
    lsof "${SERIAL_PORT}" "${LIDAR_PORT}" || true
    echo "[final processes]"
    ps -ef | grep -E "esp32_bridge|lidar_driver|wave_rover_min_actuation_probe|upper_robot_api" | grep -v grep || true
  } >"${RUN_DIR}/final_cleanup_check.log" 2>&1
}
trap cleanup EXIT

{
  echo "[connection]"
  hostname
  date
  echo "ROS_DISTRO=${ROS_DISTRO:-}"
  ros2 pkg prefix ros2_trashbot_hardware
  echo "[devices]"
  ls -l "${SERIAL_PORT}" "${LIDAR_PORT}"
  echo "[service before]"
  systemctl is-active "${SERVICE_NAME}" || true
  echo "[lsof before]"
  lsof "${SERIAL_PORT}" "${LIDAR_PORT}" || true
  echo "[processes before]"
  ps -ef | grep -E "esp32_bridge|lidar_driver|wave_rover_min_actuation_probe|upper_robot_api" | grep -v grep || true
} >"${RUN_DIR}/precheck.log" 2>&1

if [ ! -e "${SERIAL_PORT}" ] || [ ! -e "${LIDAR_PORT}" ]; then
  echo "required devices missing" >"${RUN_DIR}/precheck_failed.log"
  exit 10
fi

if systemctl is-active --quiet "${SERVICE_NAME}"; then
  # API 当前常驻但不应与本轮 bridge 争抢底盘串口，所以只在 probe 窗口内停掉。
  systemctl stop "${SERVICE_NAME}"
  STOPPED_SERVICE="true"
  sleep 1
fi

# 清掉历史遗留的同名 ROS 进程，只针对本轮需要的 executable 名称，不碰其他系统服务。
pkill -f "ros2_trashbot_hardware/lib/ros2_trashbot_hardware/esp32_bridge" || true
pkill -f "ros2_trashbot_hardware/lib/ros2_trashbot_hardware/lidar_driver" || true
pkill -f "ros2 run ros2_trashbot_hardware esp32_bridge" || true
pkill -f "ros2 run ros2_trashbot_hardware lidar_driver" || true
sleep 1

{
  echo "[after service stop]"
  systemctl is-active "${SERVICE_NAME}" || true
  echo "[lsof after service stop]"
  lsof "${SERIAL_PORT}" "${LIDAR_PORT}" || true
} >"${RUN_DIR}/after_service_stop.log" 2>&1

ros2 run ros2_trashbot_hardware lidar_driver --ros-args \
  -p serial_port:="${LIDAR_PORT}" \
  -p serial_baudrate:=150000 \
  >"${RUN_DIR}/lidar_driver.log" 2>&1 &
LIDAR_PID=$!

ros2 run ros2_trashbot_hardware esp32_bridge --ros-args \
  -p serial_port:="${SERIAL_PORT}" \
  -p serial_baudrate:=115200 \
  -p command_mode:=speed \
  -p max_wheel_speed_mps:=1.3 \
  -p feedback_interval_ms:=50 \
  -p feedback_debug_log_path:="${RUN_DIR}/wave_rover_feedback_debug.jsonl" \
  >"${RUN_DIR}/esp32_bridge.log" 2>&1 &
BRIDGE_PID=$!

sleep 4

{
  echo "[started pids]"
  echo "LIDAR_PID=${LIDAR_PID}"
  echo "BRIDGE_PID=${BRIDGE_PID}"
  echo "[service list]"
  ros2 service list | sort
  echo "[topic list]"
  ros2 topic list | sort
  echo "[lsof stack]"
  lsof "${SERIAL_PORT}" "${LIDAR_PORT}" || true
} >"${RUN_DIR}/stack_precheck.log" 2>&1

timeout 5 ros2 service call /trashbot/stop std_srvs/srv/Trigger "{}" \
  >"${RUN_DIR}/stop_precheck.log" 2>&1
STOP_STATUS=$?
if [ "${STOP_STATUS}" -ne 0 ]; then
  echo "stop precheck failed status=${STOP_STATUS}" >"${RUN_DIR}/precheck_failed.log"
  exit 20
fi

timeout 8 ros2 topic echo --once /scan >"${RUN_DIR}/scan_echo_once.log" 2>&1
SCAN_STATUS=$?
if [ "${SCAN_STATUS}" -ne 0 ]; then
  echo "scan precheck failed status=${SCAN_STATUS}" >"${RUN_DIR}/precheck_failed.log"
  exit 21
fi

PROBE_ARTIFACT_DIR="${RUN_DIR}" \
WAVE_ROVER_FEEDBACK_DEBUG="${RUN_DIR}/wave_rover_feedback_debug.jsonl" \
timeout 60 python3 "${SCRIPT_PATH}" >"${RUN_DIR}/probe_stdout.log" 2>"${RUN_DIR}/probe_stderr.log"
PROBE_STATUS=$?
echo "${PROBE_STATUS}" >"${RUN_DIR}/probe_exit_status.txt"
exit "${PROBE_STATUS}"
