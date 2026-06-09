#!/usr/bin/env bash

set -euo pipefail

# 该脚本只服务于本 sprint 的真实上车取证，不修改产品代码。
REMOTE_HOST="root@192.168.1.11"
REMOTE_PORT="37878"
SPRINT_DIR="/Users/m1/apps/rober/sprints/2026.06.10_00-45_integrated-sensor-motion-capture"
ARTIFACT_DIR="${SPRINT_DIR}/artifacts"
RUN_TS="$(date +%Y%m%d_%H%M%S)"
REMOTE_RUN_DIR="/tmp/trashbot_integrated_capture_${RUN_TS}"

# 统一把 SSH 选项收口，避免每条命令重复展开。
SSH_OPTS=(-o StrictHostKeyChecking=no -p "${REMOTE_PORT}")
SCP_OPTS=(-o StrictHostKeyChecking=no -P "${REMOTE_PORT}")

mkdir -p "${ARTIFACT_DIR}"

# 先把远端执行脚本落到 sprint artifact，便于后续核对实际步骤。
cat <<'EOF_REMOTE' > "${ARTIFACT_DIR}/remote_capture_script.sh"
#!/usr/bin/env bash

set -u

# 所有日志都写进本轮临时目录，便于一次性回收。
RUN_DIR="$1"
mkdir -p "${RUN_DIR}"
LOG_FILE="${RUN_DIR}/integrated_capture.log"

exec > >(tee -a "${LOG_FILE}") 2>&1

# ROS setup 脚本会访问未定义变量，因此 source 前暂时关闭 nounset。
set +u
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
set -u

# 明确本轮使用真实底盘串口、雷达串口和摄像头设备。
SERIAL_PORT="/dev/ttyS5"
SERIAL_BAUD="115200"
LIDAR_PORT="/dev/ttyACM0"
LIDAR_BAUD="150000"
CAMERA_DEV="/dev/video1"
ROUTE_DIR="/tmp/trashbot_integrated_sensor_motion_route"
MAP_DIR="/tmp/trashbot_integrated_sensor_motion_maps"
ROUTE_ID="integrated_sensor_motion_20260610"

mkdir -p "${RUN_DIR}/topics" "${RUN_DIR}/api"
rm -rf "${ROUTE_DIR}" "${MAP_DIR}"

BRIDGE_PID=""
LEARN_PID=""
UPPER_PID=""
ORIGINAL_UPPER_CMD=""

# 收尾必须优先停车、杀进程、恢复 API，避免串口遗留。
cleanup() {
  set +e
  source /opt/ros/humble/setup.bash
  source /root/rober/onboard/install/setup.bash
  timeout 5 ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" \
    >> "${RUN_DIR}/cleanup_zero_cmd_vel.log" 2>&1 || true
  timeout 5 ros2 service call /trashbot/stop std_srvs/srv/Trigger "{}" \
    >> "${RUN_DIR}/cleanup_stop_service.log" 2>&1 || true
  if [ -n "${LEARN_PID}" ]; then
    kill "${LEARN_PID}" 2>/dev/null || true
    wait "${LEARN_PID}" 2>/dev/null || true
  fi
  if [ -n "${BRIDGE_PID}" ]; then
    kill "${BRIDGE_PID}" 2>/dev/null || true
    wait "${BRIDGE_PID}" 2>/dev/null || true
  fi
  fuser -v "${SERIAL_PORT}" "${LIDAR_PORT}" "${CAMERA_DEV}" > "${RUN_DIR}/fuser_after_ros.txt" 2>&1 || true
  if [ -n "${ORIGINAL_UPPER_CMD}" ] || [ -n "${UPPER_PID}" ]; then
    nohup python3 /root/rober/onboard/scripts/upper_robot_api.py \
      --host 0.0.0.0 \
      --port 8787 \
      --camera-base-url http://127.0.0.1:8088 \
      --base-port /dev/ttyS5 \
      --base-baudrate 115200 \
      --max-speed 0.12 \
      > /tmp/upper_robot_api_restore.log 2>&1 &
    sleep 3
    curl -sS http://127.0.0.1:8787/api/base/status > "${RUN_DIR}/api/status_after.json" 2>&1 || true
    ps -ef | grep '[u]pper_robot_api.py' > "${RUN_DIR}/upper_robot_api_after_ps.txt" 2>&1 || true
  fi
}

trap cleanup EXIT

date > "${RUN_DIR}/date.txt"
hostname > "${RUN_DIR}/hostname.txt"
ps -ef | grep -E 'upper_robot_api|esp32_bridge|learn.launch|slam_toolbox|route_data_recorder|camera_publisher|lidar_driver|static_transform_publisher|ros2' | grep -v grep > "${RUN_DIR}/ps_before.txt" || true
curl -sS http://127.0.0.1:8787/api/base/status > "${RUN_DIR}/api/status_before.json" 2>&1 || true
fuser -v "${SERIAL_PORT}" "${LIDAR_PORT}" "${CAMERA_DEV}" > "${RUN_DIR}/fuser_before.txt" 2>&1 || true
ros2 node list > "${RUN_DIR}/ros2_node_list_before.txt" 2>&1 || true

# 只在接管底盘前停掉 upper_robot_api，避免 /dev/ttyS5 持续占用。
ps -ef | grep '[u]pper_robot_api.py' > "${RUN_DIR}/upper_robot_api_before_ps.txt" 2>&1 || true
UPPER_PID="$(ps -ef | awk '/[u]pper_robot_api.py/ {print $2; exit}')"
ORIGINAL_UPPER_CMD="$(ps -ef | awk '/[u]pper_robot_api.py/ { $1=$2=$3=$4=$5=$6=$7=""; sub(/^ +/, ""); print; exit }')"
if [ -n "${UPPER_PID}" ]; then
  kill "${UPPER_PID}"
  sleep 2
fi
fuser -v "${SERIAL_PORT}" > "${RUN_DIR}/fuser_after_api_stop.txt" 2>&1 || true

# bridge 单独启动，明确 command_mode=speed，保持与当前上车 smoke 一致。
cd /root/rober/onboard
ros2 run ros2_trashbot_hardware esp32_bridge --ros-args \
  -p serial_port:="${SERIAL_PORT}" \
  -p serial_baudrate:="${SERIAL_BAUD}" \
  -p command_mode:=speed \
  > "${RUN_DIR}/esp32_bridge.log" 2>&1 &
BRIDGE_PID="$!"
sleep 5

# learn launch 只拉传感器、SLAM、route recorder；不开 waypoint manager。
ros2 launch ros2_trashbot_bringup learn.launch.py \
  lidar_enabled:=true \
  lidar_serial_port:="${LIDAR_PORT}" \
  lidar_serial_baudrate:="${LIDAR_BAUD}" \
  static_laser_tf_enabled:=true \
  no_motion_static_odom_tf:=true \
  no_motion_mock_odom_enabled:=false \
  camera_enabled:=true \
  camera_device:="${CAMERA_DEV}" \
  route_recorder:=true \
  waypoint_manager:=false \
  route_min_distance_m:=0.01 \
  route_id:="${ROUTE_ID}" \
  route_output_dir:="${ROUTE_DIR}" \
  map_dir:="${MAP_DIR}" \
  default_map_name:=trashbot_integrated_sensor_motion_map \
  > "${RUN_DIR}/learn_launch.log" 2>&1 &
LEARN_PID="$!"
sleep 12

ros2 node list > "${RUN_DIR}/ros2_node_list_after_launch.txt" 2>&1 || true
ros2 topic info /cmd_vel > "${RUN_DIR}/cmd_vel_info.txt" 2>&1 || true
timeout 20 ros2 topic echo /scan --once > "${RUN_DIR}/topics/scan_once.txt" 2>&1 || true
timeout 20 ros2 topic echo /camera/image_raw --once > "${RUN_DIR}/topics/camera_once.txt" 2>&1 || true
timeout 20 ros2 topic echo /odom --once > "${RUN_DIR}/topics/odom_before_motion_once.txt" 2>&1 || true
timeout 15 ros2 topic echo /battery --once > "${RUN_DIR}/topics/battery_once.txt" 2>&1 || true
timeout 15 ros2 topic echo /imu/data --once > "${RUN_DIR}/topics/imu_once.txt" 2>&1 || true
ros2 service list | grep /trashbot/stop > "${RUN_DIR}/stop_service_list.txt" 2>&1 || true

# 低速短脉冲后立即归零并调用 stop 服务，符合本轮安全边界。
timeout 5 ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.03, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" \
  > "${RUN_DIR}/cmd_vel_pulse.log" 2>&1 || true
sleep 0.3
timeout 5 ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" \
  > "${RUN_DIR}/cmd_vel_zero.log" 2>&1 || true
timeout 5 ros2 service call /trashbot/stop std_srvs/srv/Trigger "{}" \
  > "${RUN_DIR}/stop_service_call.log" 2>&1 || true
sleep 2
timeout 20 ros2 topic echo /odom --once > "${RUN_DIR}/topics/odom_after_motion_once.txt" 2>&1 || true

# 保存 map，并回收 route 与 map 文件列表。
timeout 20 ros2 service call /trashbot/save_map std_srvs/srv/Trigger "{}" \
  > "${RUN_DIR}/save_map_call.log" 2>&1 || true
find "${ROUTE_DIR}" -maxdepth 3 -type f | sort > "${RUN_DIR}/route_files.txt" 2>&1 || true
find "${MAP_DIR}" -maxdepth 2 -type f | sort > "${RUN_DIR}/map_files.txt" 2>&1 || true

# 用简短等待给 route/keyframe 和 map flush 留时间。
sleep 3
find "${ROUTE_DIR}" -maxdepth 3 -type f | sort > "${RUN_DIR}/route_files_after_wait.txt" 2>&1 || true
find "${MAP_DIR}" -maxdepth 2 -type f | sort > "${RUN_DIR}/map_files_after_wait.txt" 2>&1 || true

echo "${RUN_DIR}" > "${RUN_DIR}/run_dir_path.txt"
EOF_REMOTE

chmod +x "${ARTIFACT_DIR}/remote_capture_script.sh"

scp "${SCP_OPTS[@]}" "${ARTIFACT_DIR}/remote_capture_script.sh" "${REMOTE_HOST}:${REMOTE_RUN_DIR}_script.sh" >/dev/null
ssh "${SSH_OPTS[@]}" "${REMOTE_HOST}" "bash ${REMOTE_RUN_DIR}_script.sh ${REMOTE_RUN_DIR}" | tee "${ARTIFACT_DIR}/integrated_capture_ssh.log"

# 把远端产物整体拉回本地 sprint artifact，保证文档引用可复查。
scp -r "${SCP_OPTS[@]}" "${REMOTE_HOST}:${REMOTE_RUN_DIR}" "${ARTIFACT_DIR}/remote_capture_run_${RUN_TS}" >/dev/null

# 额外抓一次恢复后的 API 状态，作为本地侧最终回读。
ssh "${SSH_OPTS[@]}" "${REMOTE_HOST}" 'curl -sS http://127.0.0.1:8787/api/base/status || true' \
  | tee "${ARTIFACT_DIR}/api_status_after.json"

printf '%s\n' "${ARTIFACT_DIR}/remote_capture_run_${RUN_TS}" > "${ARTIFACT_DIR}/latest_remote_capture_dir.txt"
