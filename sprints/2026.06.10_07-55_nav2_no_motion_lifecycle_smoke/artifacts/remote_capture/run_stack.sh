#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
cd /root/rober/onboard
RUN_DIR=/tmp/rober_20260610_0755_nav2_no_motion_lifecycle_smoke
echo $$ > "$RUN_DIR/run_stack.pid"
echo "stack_started_at=$(date --iso-8601=seconds)"
ros2 run ros2_trashbot_hardware lidar_driver --ros-args \
  -p serial_port:=/dev/ttyACM0 \
  -p serial_baudrate:=150000 \
  -p frame_id:=laser_frame \
  -p scan_topic:=/scan \
  -p raw_packet_topic:=/lidar/raw_packet \
  -p publish_raw_packets:=false \
  -p mock_scan:=false \
  > "$RUN_DIR/lidar_driver.log" 2>&1 &
echo $! > "$RUN_DIR/lidar_driver.pid"
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_link laser_frame \
  > "$RUN_DIR/static_laser_tf.log" 2>&1 &
echo $! > "$RUN_DIR/static_laser_tf.pid"
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 odom base_link \
  > "$RUN_DIR/static_odom_tf.log" 2>&1 &
echo $! > "$RUN_DIR/static_odom_tf.pid"
ros2 run nav2_map_server map_server --ros-args \
  -p use_sim_time:=false \
  -p yaml_filename:=/root/rober/onboard/runtime/maps/trashbot_map.yaml \
  > "$RUN_DIR/map_server.log" 2>&1 &
echo $! > "$RUN_DIR/map_server.pid"
ros2 run nav2_amcl amcl --ros-args \
  --params-file /root/rober/onboard/install/ros2_trashbot_nav/share/ros2_trashbot_nav/config/nav2_params.yaml \
  -p use_sim_time:=false \
  > "$RUN_DIR/amcl.log" 2>&1 &
echo $! > "$RUN_DIR/amcl.pid"
ros2 run nav2_planner planner_server --ros-args \
  --params-file /root/rober/onboard/install/ros2_trashbot_nav/share/ros2_trashbot_nav/config/nav2_params.yaml \
  -p use_sim_time:=false \
  > "$RUN_DIR/planner_server.log" 2>&1 &
echo $! > "$RUN_DIR/planner_server.pid"
ros2 run nav2_controller controller_server --ros-args \
  --params-file /root/rober/onboard/install/ros2_trashbot_nav/share/ros2_trashbot_nav/config/nav2_params.yaml \
  -p use_sim_time:=false \
  > "$RUN_DIR/controller_server.log" 2>&1 &
echo $! > "$RUN_DIR/controller_server.pid"
wait
