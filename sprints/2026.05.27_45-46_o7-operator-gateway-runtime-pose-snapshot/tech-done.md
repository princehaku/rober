# 2026.05.27 45-46 O7 Operator Gateway Runtime Pose Snapshot

## sprint_type

micro

## 实际改动

- `operator_gateway_http.py` 新增 `GET /api/o7/realtime-elevator/snapshot`，直接读取 `gateway.snapshot()`，不发送命令、不打开控制、不读取硬件。
- `operator_realtime_status.py` 新增 `trashbot.o7.realtime_elevator_snapshot.v1` board runtime pose builder：有 `robot_pose` 时返回 `operator_gateway_pose_observed`、`local_ros_pose_topic_connected=true`、`robot_pose.x_m/y_m/yaw_rad/timestamp_ms/pose_source/evidence_ref` 和按请求时间计算的 `pose_freshness.age_ms`；无 pose 或 malformed pose 时保持 `blocked_not_proven`。
- 安全边界保持：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`real_realtime_api_connected=false`、`real_ros2_tf_connected=false`、`latency_lt_2s_proven=false`，电梯状态链、楼层识别、人工接管和 route membership 仍 blocked/not_proven。
- `test_operator_gateway_http.py` 覆盖有 pose 和无 pose 两条 endpoint 路径。
- `docs/interfaces/o7_realtime_operator_console.md`、`docs/interfaces/o7_realtime_elevator_probe_api.md`、`docs/product/pc_tools_workstation.md` 同步说明 board operator gateway endpoint 与 `/amcl_pose` 语义边界。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - `Ran 59 tests in 37.615s`
  - `OK`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
  - `Ran 10 tests in 0.144s`
  - `OK`
- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_realtime_status.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
  - 通过，无输出。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_realtime_status.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/interfaces/o7_realtime_operator_console.md docs/interfaces/o7_realtime_elevator_probe_api.md docs/product/pc_tools_workstation.md sprints/2026.05.27_45-46_o7-operator-gateway-runtime-pose-snapshot`
  - 通过，无输出。

## 剩余风险

- 本轮没有真实 ROS2 runtime smoke，没有接 cloud production，没有证明 `/tf`、真实地图、电梯状态链、route membership、控制链路或 `<2s` 连续刷新。
- `pose_freshness.age_ms` 只是单次 HTTP 请求观测值；`latency_lt_2s_proven` 仍固定为 `false`。
- 需要后续在真实 operator gateway 进程中用 `/amcl_pose` 发布源做本机 loopback smoke，并把证据接入 PC probe/验收记录。
