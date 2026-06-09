#!/usr/bin/env bash
set -u

RUN_ID="20260610_0815_nav2_lifecycle_activation_probe"
RUN_DIR="/tmp/rober_${RUN_ID}"
MAP_FILE="/root/rober/onboard/runtime/maps/trashbot_map.yaml"
PARAM_FILE="${RUN_DIR}/nav2_no_motion_params.yaml"
STACK_SCRIPT="${RUN_DIR}/run_stack.sh"
STACK_PID_FILE="${RUN_DIR}/setsid_launcher.pid"

rm -rf "${RUN_DIR}"
mkdir -p "${RUN_DIR}"
cd "${RUN_DIR}" || exit 2

log_cmd() {
  local name="$1"
  shift
  {
    echo "### ${name}"
    echo "### command: $*"
    echo "### started_at: $(date --iso-8601=seconds)"
    "$@"
    local rc=$?
    echo "### exit_code: ${rc}"
    echo "### finished_at: $(date --iso-8601=seconds)"
    return "${rc}"
  } > "${RUN_DIR}/${name}.log" 2>&1
}

cat > "${PARAM_FILE}" <<'YAML'
map_server:
  ros__parameters:
    use_sim_time: false
    yaml_filename: "/root/rober/onboard/runtime/maps/trashbot_map.yaml"

amcl:
  ros__parameters:
    use_sim_time: false
    scan_topic: "/scan"
    base_frame_id: "base_link"
    odom_frame_id: "odom"
    global_frame_id: "map"
    tf_broadcast: true
    set_initial_pose: false

planner_server:
  ros__parameters:
    use_sim_time: false
    expected_planner_frequency: 20.0
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      tolerance: 0.5
      use_astar: false
      allow_unknown: true

controller_server:
  ros__parameters:
    use_sim_time: false
    controller_frequency: 20.0
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.5
    min_theta_velocity_threshold: 0.001
    progress_checker_plugin: "progress_checker"
    goal_checker_plugins: ["goal_checker"]
    controller_plugins: ["FollowPath"]
    progress_checker:
      plugin: "nav2_controller::SimpleProgressChecker"
      required_movement_radius: 0.5
      movement_time_allowance: 10.0
    goal_checker:
      plugin: "nav2_controller::SimpleGoalChecker"
      xy_goal_tolerance: 0.25
      yaw_goal_tolerance: 0.25
      stateful: true
    FollowPath:
      plugin: "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController"
      desired_linear_vel: 0.3
      lookahead_dist: 0.6
      min_lookahead_dist: 0.3
      max_lookahead_dist: 0.9
      transform_tolerance: 0.1

global_costmap:
  global_costmap:
    ros__parameters:
      use_sim_time: false
      global_frame: map
      robot_base_frame: base_link
      update_frequency: 1.0
      publish_frequency: 1.0
      width: 10
      height: 10
      resolution: 0.05
      track_unknown_space: true
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      static_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
        map_subscribe_transient_local: true
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: true
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: true
          marking: true
          data_type: "LaserScan"
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55

local_costmap:
  local_costmap:
    ros__parameters:
      use_sim_time: false
      global_frame: odom
      robot_base_frame: base_link
      update_frequency: 5.0
      publish_frequency: 1.0
      width: 3
      height: 3
      resolution: 0.05
      rolling_window: true
      plugins: ["obstacle_layer", "inflation_layer"]
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: true
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: true
          marking: true
          data_type: "LaserScan"
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55

lifecycle_manager_navigation:
  ros__parameters:
    use_sim_time: false
    autostart: true
    bond_timeout: 4.0
    node_names:
      - map_server
      - amcl
      - planner_server
      - controller_server
YAML

cat > "${STACK_SCRIPT}" <<'BASH'
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
BASH
chmod +x "${STACK_SCRIPT}"

echo "${RUN_DIR}" > "${RUN_DIR}/RUN_DIR.txt"
echo "hostname=$(hostname)" | tee "${RUN_DIR}/environment.log"
date --iso-8601=seconds | tee -a "${RUN_DIR}/environment.log"
uname -a | tee -a "${RUN_DIR}/environment.log"
echo "map_file=${MAP_FILE}" | tee -a "${RUN_DIR}/environment.log"
test -f "${MAP_FILE}" && ls -l "${MAP_FILE}" | tee -a "${RUN_DIR}/environment.log"

log_cmd pre_lsof lsof /dev/ttyS5 /dev/ttyACM0 || true
log_cmd pre_fuser fuser -v /dev/ttyS5 /dev/ttyACM0 || true
log_cmd pre_ros_graph bash -lc 'source /opt/ros/humble/setup.bash; ros2 topic list; ros2 node list'

RUN_DIR="${RUN_DIR}" PARAM_FILE="${PARAM_FILE}" setsid "${STACK_SCRIPT}" > "${RUN_DIR}/setsid_launcher.log" 2>&1 &
STACK_PGID=$!
echo "${STACK_PGID}" > "${STACK_PID_FILE}"
echo "stack_pgid=${STACK_PGID}" | tee "${RUN_DIR}/stack_pgid.log"

sleep 12

log_cmd lifecycle_get_before_manual bash -lc 'source /opt/ros/humble/setup.bash; for n in /map_server /amcl /planner_server /controller_server; do echo "## $n"; ros2 lifecycle get "$n" || true; done'
log_cmd lifecycle_manual_configure bash -lc 'source /opt/ros/humble/setup.bash; for n in /map_server /amcl /planner_server /controller_server; do echo "## configure $n"; timeout 12 ros2 lifecycle set "$n" configure || true; done'
sleep 4
log_cmd lifecycle_manual_activate bash -lc 'source /opt/ros/humble/setup.bash; for n in /map_server /amcl /planner_server /controller_server; do echo "## activate $n"; timeout 12 ros2 lifecycle set "$n" activate || true; done'
sleep 8
log_cmd lifecycle_get_after_activate bash -lc 'source /opt/ros/humble/setup.bash; for n in /map_server /amcl /planner_server /controller_server; do echo "## $n"; ros2 lifecycle get "$n" || true; done'
log_cmd ros_graph_during_runtime bash -lc 'source /opt/ros/humble/setup.bash; ros2 topic list; ros2 node list; ros2 topic info /cmd_vel -v || true'
log_cmd scan_once bash -lc 'source /opt/ros/humble/setup.bash; timeout 8 ros2 topic echo --once /scan'
log_cmd map_once bash -lc 'source /opt/ros/humble/setup.bash; timeout 8 ros2 topic echo --once --qos-durability transient_local /map'
log_cmd amcl_pose_once bash -lc 'source /opt/ros/humble/setup.bash; timeout 8 ros2 topic echo --once /amcl_pose'
log_cmd cmd_vel_echo bash -lc 'source /opt/ros/humble/setup.bash; timeout 8 ros2 topic echo /cmd_vel'
log_cmd cmd_vel_hz bash -lc 'source /opt/ros/humble/setup.bash; timeout 8 ros2 topic hz /cmd_vel'
log_cmd api_nav2_proof_refresh bash -lc 'curl --max-time 150 -sS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh -H "Content-Type: application/json" -d "{\"timeout_s\":20}"'
log_cmd api_nav2_proof_latest bash -lc 'curl -sS http://127.0.0.1:8787/api/nav2/proof/latest'
log_cmd api_nav2_status bash -lc 'curl -sS http://127.0.0.1:8787/api/nav2/status'

echo "cleanup_started_at=$(date --iso-8601=seconds)" | tee "${RUN_DIR}/cleanup.log"
kill -TERM "-${STACK_PGID}" >> "${RUN_DIR}/cleanup.log" 2>&1 || true
sleep 4
kill -KILL "-${STACK_PGID}" >> "${RUN_DIR}/cleanup.log" 2>&1 || true
sleep 2
log_cmd final_process_check bash -lc 'ps -eo pid,pgid,stat,cmd | grep -E "rober_20260610_0815_nav2_lifecycle_activation_probe|lidar_driver|map_server|amcl|planner_server|controller_server|lifecycle_manager|static_transform_publisher" | grep -v grep || true'
log_cmd final_lsof lsof /dev/ttyS5 /dev/ttyACM0 || true
log_cmd final_fuser fuser -v /dev/ttyS5 /dev/ttyACM0 || true

cp /root/rober/onboard/runtime/nav2_lifecycle_latest.json "${RUN_DIR}/onboard_runtime_nav2_lifecycle_latest.json" 2>"${RUN_DIR}/copy_nav2_lifecycle_latest.stderr" || true
find "${RUN_DIR}" -maxdepth 1 -type f -printf "%f\n" | sort > "${RUN_DIR}/FILES.txt"
tar -C "$(dirname "${RUN_DIR}")" -czf "/tmp/${RUN_ID}.tgz" "$(basename "${RUN_DIR}")"
echo "/tmp/${RUN_ID}.tgz"
