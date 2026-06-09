# Nav2 no-motion lifecycle smoke

- sprint_type: micro
- owner: robot-algorithm-engineer
- 远端: `root@192.168.1.11 -p 37878`
- 时间: 2026-06-10 05:27-05:33 CST

## 实际改动

- 新增本轮远端 artifacts:
  - `artifacts/remote_capture/preflight.log`
  - `artifacts/remote_capture/ros_graph_during_runtime.log`
  - `artifacts/remote_capture/api_nav2_proof_refresh_response.json`
  - `artifacts/remote_capture/api_nav2_proof_latest_response.json`
  - `artifacts/remote_capture/api_nav2_status_response.json`
  - `artifacts/remote_capture/onboard_runtime_nav2_lifecycle_latest.json`
  - `artifacts/remote_capture/final_cleanup.log`
  - `artifacts/remote_capture/*_server.log`、`lidar_driver.log`、`static_*_tf.log`
  - `artifacts/remote_capture/apt_get_sim_install_nav2_bringup.txt`
  - `artifacts/remote_capture/apt_cache_policy_nav2_bringup_stack.txt`
- 更新 `docs/hardware/board_sensor_stack_smoke.md`，记录本轮 no-motion Nav2 lifecycle smoke。
- 更新 `docs/navigation/fixed_route_workflow.md`，补充 Nav2 runtime smoke 的前置与边界。
- 未修改产品代码、launch、参数、硬件配置或 firmware。

## 远端启动方式

本轮未使用 `autonomous.launch.py`，未启动 `esp32_bridge`、`task_orchestrator` 或任何 goal/path execution。第一次按建议路径尝试 `nav2_bringup` 前先做包检查，结果：

```text
pkg nav2_bringup: Package not found
pkg nav2_lifecycle_manager: Package not found
pkg nav2_amcl: /opt/ros/humble
pkg nav2_planner: /opt/ros/humble
pkg nav2_controller: /opt/ros/humble
pkg nav2_map_server: /opt/ros/humble
pkg nav2_navfn_planner: Package not found
pkg nav2_regulated_pure_pursuit_controller: Package not found
pkg nav2_costmap_2d: /opt/ros/humble
```

因此本轮没有安装 `ros-humble-nav2-bringup`。`apt-get -s install ros-humble-nav2-bringup` 显示：

```text
5 upgraded, 164 newly installed, 0 to remove and 317 not upgraded.
```

该结果会拉入完整 `ros-humble-navigation2`、OpenCV/GDAL 等大量依赖，并升级 Kerberos/libsodium，超过本轮“最小安全修复、不升级全系统”的边界。

随后启动一个 `/tmp` 独立进程组做 fallback smoke，进程组根 PID/PGID 为 `124092`：

```bash
ros2 run ros2_trashbot_hardware lidar_driver --ros-args \
  -p serial_port:=/dev/ttyACM0 \
  -p serial_baudrate:=150000 \
  -p frame_id:=laser_frame \
  -p scan_topic:=/scan \
  -p publish_raw_packets:=false \
  -p mock_scan:=false
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_link laser_frame
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 odom base_link
ros2 run nav2_map_server map_server --ros-args \
  -p use_sim_time:=false \
  -p yaml_filename:=/root/rober/onboard/runtime/maps/trashbot_map.yaml
ros2 run nav2_amcl amcl --ros-args --params-file \
  /root/rober/onboard/install/ros2_trashbot_nav/share/ros2_trashbot_nav/config/nav2_params.yaml \
  -p use_sim_time:=false
ros2 run nav2_planner planner_server --ros-args --params-file \
  /root/rober/onboard/install/ros2_trashbot_nav/share/ros2_trashbot_nav/config/nav2_params.yaml \
  -p use_sim_time:=false
ros2 run nav2_controller controller_server --ros-args --params-file \
  /root/rober/onboard/install/ros2_trashbot_nav/share/ros2_trashbot_nav/config/nav2_params.yaml \
  -p use_sim_time:=false
```

两个 static TF 都是 smoke-only 零位姿：`base_link -> laser_frame` 和 `odom -> base_link`，不代表机械标定或真实里程计。

## 验证结果

远端 package/source 检查：

```text
hostname: op-z3-b6.home
date: Wed Jun 10 05:30:34 AM CST 2026
map: /root/rober/onboard/runtime/maps/trashbot_map.yaml
params: /root/rober/onboard/install/ros2_trashbot_nav/share/ros2_trashbot_nav/config/nav2_params.yaml
pre_lsof: no output
pre_fuser: no output
```

runtime ROS graph 证明 fallback 节点确实起来：

```text
/amcl
/controller_server
/global_costmap/global_costmap
/lidar_driver
/local_costmap/local_costmap
/map_server
/planner_server
/scan
/tf_static
```

read-only lifecycle 状态：

```text
lifecycle /map_server: unconfigured [1]
lifecycle /amcl: unconfigured [1]
lifecycle /planner_server: unconfigured [1]
lifecycle /controller_server: unconfigured [1]
```

正式 collector:

```bash
curl -sS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh \
  -H 'Content-Type: application/json' \
  -d '{"timeout_s":20}'
curl -sS http://127.0.0.1:8787/api/nav2/proof/latest
curl -sS http://127.0.0.1:8787/api/nav2/status
```

`onboard_runtime_nav2_lifecycle_latest.json` 结果：

```text
status=blocked_with_root_cause
map_server_active=false
amcl_active=false
planner_active=false
controller_active=false
scan_once_observed=true
map_once_observed=false
amcl_pose_observed=false
path_generation_ready=false
publishes_cmd_vel=false
calls_base_manual=false
uses_base_uart=false
delivery_success=false
```

本轮消失的 blocker：

- `/scan_once_not_observed` 已消失；collector 成功 echo 到 `/scan`，frame_id 为 `laser_frame`。

仍存在的 blocker：

- `map_server_lifecycle_not_active`
- `amcl_lifecycle_not_active`
- `planner_lifecycle_not_active`
- `controller_lifecycle_not_active`
- `/map_once_not_observed`
- `/amcl_pose_once_not_observed`

新增/更明确的 root cause：

- `nav2_bringup` 缺失，无法按正式 `nav2_bringup bringup_launch.py` 启动。
- `nav2_lifecycle_manager` 缺失，手工启动 lifecycle nodes 后无法自动 transition 到 active。
- `nav2_navfn_planner` 与 `nav2_regulated_pure_pursuit_controller` 缺失，当前 `nav2_params.yaml` 指定的 planner/controller 插件在完整 Nav2 active 阶段仍会阻塞。

## 清理结果

清理方式：

```bash
kill -TERM -- -124092
sleep 5
kill -KILL -- -124092
```

final 结果：

```text
process_check_after_kill: no output
final_lsof: no output
final_fuser: no output
```

`lidar_driver.log` 在 SIGTERM 清理窗口出现 `publisher's context is invalid` / `rcl_shutdown already called` traceback；这是 shutdown race，不影响 final 无残留和串口释放结论。

## 安全边界

- 未发布 `/cmd_vel`。
- 未调用 `/api/base/*`、`/api/map/start`、`/api/nav2/start`、`/api/nav2/stop`。
- 未调用 `ros2 action send_goal`。
- 未调用 compute path 或 lifecycle transition service。
- 未发布 `/initialpose`。
- 未打开 WAVE ROVER/base UART `/dev/ttyS5`，只做 pre/final `lsof/fuser`。
- 只允许 LiDAR `/dev/ttyACM0` 被本轮 `lidar_driver` 打开，结束后已释放。

## 剩余风险

- 本轮不是 Nav2 ready、AMCL localization、path generation、fixed-route execution 或 delivery_success。
- `/amcl_pose` 未观测在 no initial pose/no active AMCL 条件下是有效 blocker；本轮按边界未发布 `/initialpose`。
- 要继续推进正式 lifecycle active，需要先决定是否安装完整 Nav2 bringup/lifecycle/plugin 栈，或改成项目自有最小 lifecycle manager/参数栈；安装前必须再次 dry-run 并控制系统升级范围。
- pre ROS graph 中仍有历史重名 `/map_recorder`、`/task_orchestrator`、`/waypoint_manager`，本轮只记录不清理。
