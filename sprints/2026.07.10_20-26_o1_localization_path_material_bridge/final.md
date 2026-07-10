# O1 Localization Path Material Bridge Final

## sprint_type

sprint_type: epic

## 收口摘要

本轮 `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/` 完成 O1 `localization_path_material_bridge` 产品收口。Hardware owner 已扩展 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，消费 `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/38_pc_summary_after_map_fix.json` 的 same-run localization/path readback，并在主会话退回后补齐 optional dangerous true 的 fail-closed 缺口。

Product 判断：O1 可从约 `89%` 保守上调到约 `90%`。本轮确实新增了同 run localization/path material delta，而不是重复 free-cell wrapper；但 same-run path 仍明确失败，因此不能再上调更多，也不能归档 KR。

## 用户价值和产品北极星

用户最终需要普通手机用户可安全、可验证地完成垃圾送达。本 sprint 的直接用户价值是把“历史同 run free-cell map material”推进到“同 run localization readiness 已读到、path generation 仍未成功”的可复验材料链，让下一轮现场执行命令知道具体缺口。

产品北极星不变：低成本 ROS2 自主垃圾投递机器人，用户把垃圾交给小车后，小车沿固定路线送到垃圾站点位，并且全过程可观测、可回放、可解释。

## OKR 映射和方向判断

- O1：继续，约 `89% -> 90%`。本轮消费 `38_pc_summary_after_map_fix.json` 的 same-run localization/path readback，并 fail-closed 固定 `same_run_path_proven=false`。
- O5：暂停计分，保持约 `85%`。O5 仍是最低 Objective，但当前没有真实 external production evidence，上一轮 O5 packet 已明确 `okr_credit_allowed=false`，本轮不能因为 support-only/readiness surface 涨分。
- O6/O7：保持约 `91%`。本轮没有新增 O6 archive/readback 或 O7 UI/consumer 交付。

方向判断：继续 O1 现场证据链，但下一步必须进入 current live HIL、current same-run path generation 或 route execution material；O5 下一次只有真实 production external evidence 才允许 OKR 增量。

## Product 核心抓手

核心抓手是把 `localization_path_material_bridge` 固化为可验收的 O1 material bridge：

- `localization_path_material_bridge_present=true`
- `same_run_path_generation_requested=true`
- `same_run_path_generation_succeeded=false`
- `same_run_path_generated=false`
- `same_run_path_point_count=0`
- `same_run_path_proven=false`
- `cross_run_clean_baseline_path_summary.path_point_count=31`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `nav2_route_execution_success=false`

## 实际改动

Hardware owner 已完成并记录：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/tech-done.md`

Product closeout 本轮新增或更新：

- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/side2side_check.md`
- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/final.md`
- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/artifacts/product_worker_report.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Hardware `tech-done.md` 记录的最终验证：

```text
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
passed
```

```text
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
Ran 24 tests in 0.104s
OK
```

```text
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
exit 0
localization_path_material_bridge_present=true
same_run_path_generation_requested=true
same_run_path_generation_succeeded=false
same_run_path_generated=false
same_run_path_point_count=0
same_run_path_proven=false
cross_run_clean_baseline_path_summary.path_point_count=31
hil_pass=false
safe_to_control=false
delivery_success=false
primary_actions_enabled=false
robot_control_executed=false
nav2_route_execution_success=false
```

```text
rg anchor check passed
git diff --check passed
```

Product closeout 验证命令见本轮最终回复。

## 失败定位

主会话曾退回一个 fail-closed 缺口：endpoint `key_values` 只检查了 `safe_to_control`、`delivery_success`、`primary_actions_enabled`，没有覆盖 optional dangerous fields。Hardware owner 已修复：`robot_control_executed`、`hil_pass`、`nav2_route_execution_success`、`same_run_path_proven`、`wheel_feedback_lr_nonzero_proven`、`real_route_map_proven` 等字段缺失不误杀正例，但出现且不是 `false` 会 blocked。Comparator 侧也补了 `latest_result.primary_actions_enabled=true` 的禁用回归。

修复后 24 个 motion/map/HIL bundle tests 通过，当前没有遗留失败。

## Proof Boundary

proof boundary：`software_proof_o1_motion_map_hil_material_bundle_only` / historical same-run software proof only。

本轮不是：

- current live HIL
- safe-to-control
- delivery success
- same-run path generation success
- Nav2 route execution success
- wheel direction proof
- IMU/battery calibration proof
- production cloud proof

## KR 更新和历史归档

本轮不归档任何 KR。原因是 O1 仍缺 current live HIL、wheel direction、IMU/battery calibration、current same-run path success 和 route execution success；O5 仍缺真实 external production evidence。

历史记录位置：

- `OKR.md` O1 当前进度段和 4.1 快照
- `docs/process/okr_progress_log.md` 顶部 2026-07-10 系列
- 本 sprint `side2side_check.md` / `final.md`

## 剩余风险

- 仍缺 current same-run `feedback_T1001.log`、motion command record、operator/external observation、HIL acceptance record。
- 仍缺 current same-run Nav2 path generation success 和 route execution success。
- June 11 clean-baseline `path_point_count=31` 只是 cross-run comparator，不能替代本 run 的 path proof。
- O5 虽为最低 Objective，但无真实 production external evidence，继续做 readiness/support packet 只能回归守护，不能计主 OKR。

## 下一轮建议

优先 O1 current live material：采集 current same-run HIL acceptance、WAVE ROVER feedback、motion command、operator/external observation，并把 localization/path bridge 接到真实 Nav2 path generation / route execution readback。若 CEO 能提供 O5 production evidence，则切回 O5 external production proof；否则不要继续消费 O5 support-only surface。
