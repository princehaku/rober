# O3 Rclpy Scan Runtime Repair Final

## Sprint Summary

- Sprint: `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/`
- Sprint type: `epic`
- Owner: `robot-algorithm-engineer`
- Product closeout: `product-okr-owner`

本轮目标是修复或绕开上一轮 `/scan` rclpy probe 的 `librcl_action.so` / `_rclpy_pybind11` ImportError，并在真实板 no-motion 窗口内证明 `/scan` frame observed，或把失败收敛到更可执行的 root cause。

## 用户价值和产品北极星

用户价值：让固定路线送垃圾从历史材料和 wrapper/readback 证明，继续靠近当前现场可生成路线的事实链。

产品北极星：普通手机用户交付垃圾后，小车能安全、可验证地沿固定路线完成投递。本轮只推进路线生成前置诊断，不等于手机侧送达闭环、真实控制或 HIL 完成。

## 实际改动

Algorithm owner 已完成实现与 `tech-done.md` 留档，核心改动为：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`：将 `/scan` `rclpy_sensor_data_once` 迁移到 ROS-sourced child Python probe，新增 `environment_check`、`import_check`、`runtime_diagnostics`、`fallback_boundary`、`frame_observed`、`frame_stamp` 等 additive artifact 字段。
- `onboard/tests/test_nav2_runtime_proof_helper.py`：覆盖 child probe command、import failure 分类、child timeout after import root cause 和 no-motion safety guard。
- `docs/navigation/field_route_evidence_preflight.md`、`docs/navigation/fixed_route_workflow.md`：同步记录 14:42 artifact 的读取顺序和证据边界。
- 本 sprint artifacts：新增 local fail-closed artifact 与真实板 live artifact。

Product closeout 本轮新增：

- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/side2side_check.md`
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Engineer 已记录的验证结果：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`：exit `0`
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`：`Ran 55 tests in 2.191s OK`
- Local helper：exit `2`，按预期 fail-closed，原因包括 `map_lifecycle_latest_missing`、`ros2_command_unavailable_after_bash_source`
- `scp` 到真实板：exit `0`
- Live helper：exit `2`，真实板 no-motion proof fail-closed 并写出 live artifact
- 拉回 live artifact：exit `0`
- Scoped `git diff --check`：exit `0`

Live artifact 关键字段：

- `/scan.topic_type=sensor_msgs/msg/LaserScan`
- `/scan.probe.observed=false`
- `/scan.probe.best_attempt.label=rclpy_sensor_data_once`
- `/scan.probe.best_attempt.runtime=ros_sourced_child_python`
- `import_check.ok=true`
- Root cause: `/scan_rclpy_child_timeout_after_import`
- CLI fallback 仍 timeout
- `/amcl_pose=false`
- `map_to_odom=false`
- `path_generated=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

## OKR 映射和方向判断

- O5：继续暂停 support-only 追分，保持约 `~85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 或真实手机/browser evidence。
- O1：继续现场 localization/path 前置链路，保持约 `~93%`。本轮有新诊断进展，但没有 current same-run path generation success、Nav2 route execution success、current live HIL pass、safe-to-control 或 delivery success。
- O6/O7：继续等待 current-run material，均保持约 `~93%`。本轮没有新的 `task_id`、`map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、Nav2 result、delivery record、operator confirmation 或 production readback。

方向判断：继续 O3/O1 live path 前置链路，不回到 O5 support-only，也不继续修旧的 main-process rclpy ImportError。下一轮应直指 LiDAR publisher/sample timing/endpoint inventory。

## KR 拆解、更新或历史归档

- O1 current same-run path generation：仍 blocked，`path_generated=false`。
- O6/O7 current-run material：仍 blocked，没有新路线/回放/送达/operator material 可消费。
- O5 production evidence：仍 blocked，没有真实 external production evidence。
- 已完成 KR 历史归档：无新增。

结论：本轮不归档 KR，不调整 O5/O1/O6/O7 百分比。

## 剩余风险

- `/scan` import 成功不等于 frame observed；`/scan_rclpy_child_timeout_after_import` 表明 child subscriber 在窗口内没有拿到 LaserScan sample。
- CLI fallback 也 timeout，LiDAR publisher 连续发布、QoS、endpoint visibility 或 managed runtime sample timing 仍是下一轮第一风险。
- `/amcl_pose=false`、`map_to_odom=false`、`path_generated=false` 会继续阻塞 same-run path generation。
- `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false` 必须继续保持，不能扩大为运动、HIL 或 delivery proof。

## 下一轮建议

下一轮由 `robot-algorithm-engineer` 主责，优先做 `/scan` publisher/sample timing/endpoint inventory：

1. 在 child rclpy timeout 前后抓取 `/scan` publisher count、endpoint QoS、publisher node、sample rate 和 last sample timing。
2. 对比 LiDAR driver managed runtime 是否在 helper probe 窗口内实际启动并持续发布。
3. 若 endpoint 存在但 sample timeout，调 QoS/window；若 endpoint 缺失，回到 LiDAR publisher lifecycle / launch 参数。
4. `/scan` observed 后再复验 `/amcl_pose`、dynamic `map->odom` 和 `path_generated=true`。

不得把下一轮重点退回旧的 main-process rclpy ImportError；不得回到 O5 readiness/support-only packet 追分。
