#!/usr/bin/env bash
# ROS 的 setup.bash 会读取未预置的环境变量；这里不启用 nounset，避免证据脚本早退。
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
cd /root/rober/onboard || exit 2

RUN_DIR="${RUN_DIR:?missing RUN_DIR}"
PARAM_FILE="${PARAM_FILE:?missing PARAM_FILE}"
echo "stack_shell_pid=$$" > "${RUN_DIR}/stack_supervisor.log"
echo "stack_started_at=$(date --iso-8601=seconds)" >> "${RUN_DIR}/stack_supervisor.log"

ros2 run ros2_trashbot_hardware lidar_driver --ros-args \
  -p serial_port:=/dev/ttyACM0 \
  -p serial_baudrate:=150000 \
  -p frame_id:=laser_frame \
  -p scan_topic:=/scan \
  -p raw_packet_topic:=/lidar/raw_packet \
  -p publish_raw_packets:=false \
  -p mock_scan:=false \
  > "${RUN_DIR}/lidar_driver.log" 2>&1 &
echo $! > "${RUN_DIR}/lidar_driver.pid"

ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_link laser_frame \
  > "${RUN_DIR}/static_laser_tf.log" 2>&1 &
echo $! > "${RUN_DIR}/static_laser_tf.pid"

ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 odom base_link \
  > "${RUN_DIR}/static_odom_tf.log" 2>&1 &
echo $! > "${RUN_DIR}/static_odom_tf.pid"

ros2 run nav2_map_server map_server --ros-args --params-file "${PARAM_FILE}" \
  > "${RUN_DIR}/map_server.log" 2>&1 &
echo $! > "${RUN_DIR}/map_server.pid"

ros2 run nav2_amcl amcl --ros-args --params-file "${PARAM_FILE}" \
  > "${RUN_DIR}/amcl.log" 2>&1 &
echo $! > "${RUN_DIR}/amcl.pid"

ros2 run nav2_planner planner_server --ros-args --params-file "${PARAM_FILE}" \
  > "${RUN_DIR}/planner_server.log" 2>&1 &
echo $! > "${RUN_DIR}/planner_server.pid"

ros2 run nav2_controller controller_server --ros-args --params-file "${PARAM_FILE}" \
  > "${RUN_DIR}/controller_server.log" 2>&1 &
echo $! > "${RUN_DIR}/controller_server.pid"

ros2 run nav2_lifecycle_manager lifecycle_manager --ros-args \
  -r __node:=lifecycle_manager_navigation \
  --params-file "${PARAM_FILE}" \
  > "${RUN_DIR}/lifecycle_manager.log" 2>&1 &
echo $! > "${RUN_DIR}/lifecycle_manager.pid"

wait
