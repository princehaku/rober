# O3 AMCL TF Bringup Repair Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的主 Objective 是 O5，约 `~85%`。
2. 本 sprint 不直接推进 O5。
3. 转向理由：最近 O5 已因缺真实 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic 和真实 phone/browser evidence 固定 `okr_credit_allowed=false`。继续 O5 readiness/probe/wrapper 会重复消费 `no_real_production_external_evidence` blocker。本轮继续现场 O3 lane，直接修 AMCL/TF，以解锁后续同轮 path/material。

## Owner 与分工

- `robot-algorithm-engineer` 单线闭环：修复 no-motion AMCL/TF bringup，复跑本地测试和真实板 refresh/preflight，更新 `tech-done.md`。
- 主节点：派单、验收、汇总 `side2side_check.md` / `final.md`。

## 文件范围

允许修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `onboard/tests/test_upper_robot_api.py`
- `onboard/src/ros2_trashbot_nav/config/nav2_params.yaml`
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/tech-done.md`
- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/**`

不得修改：

- O5/O6/O7 relay、archive、PC workstation 或 cloud readiness 文件。
- WAVE ROVER 底盘协议、速度映射、默认运动入口。
- 其他 sprint 目录，除非只读引用。

## 技术方案

1. 优先修 `/initialpose` 发布稳定性：若当前 `ros2 topic pub --once /initialpose` 在真实板上容易 timeout，改为 helper 内部 rclpy publisher，等待 `/initialpose` subscriber 后短窗口重复发布，并把 subscriber count、publish attempts、elapsed、error 写入 artifact。
2. 保留 CLI fallback，但 fallback 不能覆盖 rclpy 成功事实；失败时要区分 `subscriber_missing`、`ros_python_runtime_unavailable`、`publish_timeout`、`amcl_pose_not_observed_after_publish`。
3. 强化 AMCL/TF 复盘字段：`initialpose_publish_method`、`initialpose_subscriber_count`、AMCL params、AMCL publishers/subscribers、`/tf` source inventory、`amcl_log_tail`。
4. 复跑 no-motion `/api/nav2/proof/refresh`，仅在 AMCL/TF 成立后继续 ComputePathToPose path generation。

## 接口边界

- `/initialpose` 是本轮唯一允许写入 ROS graph 的 topic，作用仅为 AMCL localization seed。
- `managed_runtime_opt_in=true` 可启动 map_server、AMCL、planner_server、LiDAR 和静态 TF，但不能启动业务导航节点。
- `path_generation_opt_in=true` 只允许 ComputePathToPose，不允许 NavigateToPose goal。
- 所有输出必须继续 fail-closed：`safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。

## 验收命令

子 agent 必须运行并汇报结果：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py
```

```bash
python3 -m unittest onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
```

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test
```

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/local_preflight.raw.json
```

若真实上位机可达，必须先保持 no-motion stop/start/status/refresh/stop 安全序列，再运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/live_amcl_tf_bringup_repair.raw.json
```

最后运行：

```bash
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_upper_robot_api.py onboard/src/ros2_trashbot_nav/config/nav2_params.yaml onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair
```

## 风险与回滚

- 若真实板不可达，只能保留 local dry-run 与不可达原因，不宣称现场修复有效。
- 若 AMCL 仍不发布 `map->odom`，本轮不调整 OKR 百分比，但必须把新的 root cause 写入 `tech-done.md`。
- 若任何验证显示会发布 `/cmd_vel`、调用 `/api/base/manual` 或执行 NavigateToPose goal，必须立即 fail-closed 并修复。
