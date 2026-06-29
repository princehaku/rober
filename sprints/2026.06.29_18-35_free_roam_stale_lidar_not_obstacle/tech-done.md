# 自由移动不受过期雷达近障碍值劫持

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py`：近障碍避让只使用新鲜雷达距离；雷达过期时 `obstacle_clear` 只标记为 `not_proven`，不再把旧的近距离值当成当前障碍触发原地避让。
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy_node.py`：修正 snapshot 注释，明确缺实时雷达只降级建图和避障证据，不锁低速自由移动。
- `onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py`、`onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py`：新增旧雷达近障碍值不触发避让的离线策略和节点 artifact 测试。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录“过期雷达距离不再阻止低速自由移动”的产品/安全口径。

## 验证结果

- 通过：`python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py`，17 个测试通过。
- 通过：`python3 -m unittest onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy.py onboard/src/ros2_trashbot_nav/test/test_free_roam_autonomy_node.py onboard/scripts/test_upper_robot_api_free_roam.py`，20 个测试通过。
- 通过：`python3 -m py_compile onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy.py onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/free_roam_autonomy_node.py onboard/scripts/upper_robot_api.py`。
- 通过：`PYTHONPATH=onboard/src/ros2_trashbot_nav python3 -m ros2_trashbot_nav.free_roam_autonomy --snapshot-json ...`，旧 `lidar_min_distance_m=0.04` 且 `lidar_age_s=120.0` 时输出 `state=running`、`linear_x_mps=0.12`、`angular_z_radps=0.0`、`stop_required=false`。
- 通过：`git diff --check`。
- 上位机离线验证：已用 `scp -P 37878` 同步 `free_roam_autonomy.py` 和 `free_roam_autonomy_node.py` 到 `root@192.168.1.11:/root/rober/onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/`，随后在上位机只运行离线 CLI 快照：
  `PYTHONPATH=/root/rober/onboard/src/ros2_trashbot_nav python3 -m ros2_trashbot_nav.free_roam_autonomy --snapshot-json ...`。
  旧 `lidar_min_distance_m=0.04`、`lidar_age_s=120.0` 场景返回 `state=running`、`linear_x_mps=0.12`、`angular_z_radps=0.0`、`stop_required=false`，没有重启 ROS2 节点，也没有发布 `/cmd_vel`。

## 剩余风险

- 本轮未发送真实运动命令；只验证策略和节点 artifact 合同。真实“车已移动”仍需要现场安全确认后跑自由移动或键盘手控，并证明 wheel raw L/R 非零。
- Nav2 上一轮 live 证据仍是 action/path 成功但 wheel raw L/R 为 0/0；完整自动驾驶运动闭环还没完成。
