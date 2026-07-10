# O1 Manual HIL Gate Current Evidence Intake Final

## sprint_type

sprint_type: epic

## 复盘结论

本轮 `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/` 完成 Product closeout。Hardware owner 已在现有 O1 bundle 中新增 `manual_hil_gate_current_evidence_material`，把 2026-06-11 历史真实 PC proxy / real-board manual gate 材料接入 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`。

Product 判断：O1 可从约 `~91%` 保守上调到约 `~92%`。这次增量来自不同于上一轮 bounded-motion 的 historical real-board / PC proxy manual gate material delta，不是 current live HIL pass，不是 safe-to-control，不是 delivery success，也不是 Nav2 route execution success。本轮不归档 KR。

## 用户价值和产品北极星

用户最终需要普通手机用户可安全、可验证地完成垃圾送达。本 sprint 的用户价值，是把一次真实 manual gate / stop safety / feedback readback / operator claim 材料收束成可复验、可脱敏、可 fail-closed 的硬件证据链，让下一次现场短动 HIL 不必再从散乱 JSON 猜测“现在到底卡在哪一层”。

产品北极星不变：低成本 ROS2 自主垃圾投递机器人，用户把垃圾交给小车后，小车沿固定路线送到垃圾站点位，并且全过程可观测、可回放、可解释。

## OKR 映射和方向判断

- O1：继续，约 `~91% -> ~92%`。本轮消费新的 manual gate current evidence material，并保持 false safety/HIL fields。
- O5：暂停计分，保持约 `~85%`。O5 仍是最低 Objective，但 `cloud_production_cutover_readiness_packet` 已固定 `okr_credit_allowed=false`，当前没有真实 external production evidence。
- O6/O7：保持约 `~92%`。本轮没有新增 O6 archive/readback 或 O7 UI/consumer 交付。

方向判断：继续 O1 现场证据链。下一步必须采 current live `feedback_T1001.log`、motion command record、operator observation、external video、LiDAR motion delta、HIL acceptance record，并把 current localization/path 接到真实 path generation 或 route execution proof。O5 只有真实 production external evidence 到位时才重新计分。

## Product 核心抓手

核心抓手是把 `manual_hil_gate_current_evidence_material` 固化为 O1 material bundle 的可验收 additive section：

- `manual_hil_gate_current_evidence_material_present=true`
- `manual_hil_gate_status=blocked`
- `manual_hil_gate_missing_fields=[external_video_recorded, visible_content_proven, wheel_feedback_lr_nonzero_proven, physical_motion_lidar_delta_proven]`
- `stop_safety_smoke_forwarded=true`
- `manual_nonstop_local_reject_present=true`
- `manual_nonstop_remote_base_manual_called=false`
- `proxy_remote_base_manual_not_called_by_local_reject=true`
- `manual_gate_t1001_observed_count=2`
- `operator_structured_delivery_claim_material_only=true`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`

## 实际改动

Hardware owner 已完成并记录：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/tech-done.md`

Product closeout 本轮新增或更新：

- `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/side2side_check.md`
- `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/final.md`
- `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/artifacts/product_worker_report.md`
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
Ran 33 tests in 0.246s
OK
```

```text
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
exit 0
status=motion_map_hil_material_bundle_ready_not_hil_pass
manual_hil_gate_current_evidence_material_present=true
manual_hil_gate_status=blocked
manual_gate_t1001_observed_count=2
proxy_remote_base_manual_not_called_by_local_reject=true
hil_pass=false
safe_to_control=false
delivery_success=false
```

Product closeout 验证命令见 `artifacts/product_worker_report.md` 和最终回复。

## 失败定位

Hardware `tech-done.md` 记录：首轮验收无失败；`py_compile`、单测、CLI、anchor `rg` 和 scoped `git diff --check` 均一次通过。Product closeout 未发现新增失败。

## Proof Boundary

Proof boundary：`software_proof_o1_motion_map_hil_material_bundle_only` / historical upper-computer software proof only。

本轮不是：

- current live HIL
- safe-to-control
- delivery success
- manual gate 已通过
- wheel feedback L/R 非零 proof
- wheel direction proof
- IMU/battery calibration proof
- same-run path generation success
- Nav2 route execution success
- production cloud proof

## KR 更新和历史归档

本轮不归档任何 KR。原因是 O1 仍缺 current live HIL、wheel direction、IMU/battery calibration、same-run path success、route execution success 和 hardware safety acceptance；O5 仍缺真实 external production evidence。

历史记录位置：

- `OKR.md` O1 当前进度段和 4.1 快照
- `docs/process/okr_progress_log.md` 顶部 2026-07-10 系列
- 本 sprint `side2side_check.md` / `final.md` / `artifacts/product_worker_report.md`

## 剩余风险

- 仍缺 `external_video_recorded`
- 仍缺 `visible_content_proven`
- 仍缺 `wheel_feedback_lr_nonzero_proven`
- 仍缺 `physical_motion_lidar_delta_proven`
- 仍缺 current same-run `feedback_T1001.log`、motion command record、operator/external observation、HIL acceptance record
- 仍缺 current same-run Nav2 path generation success 和 route execution success
- O5 虽为最低 Objective，但无真实 production external evidence，继续做 readiness/support packet 只能回归守护，不能计主 OKR

## 下一轮建议

优先 O1 current live material：采集 current same-run HIL acceptance、WAVE ROVER T1001 feedback、motion command、operator/external observation、external video 和 LiDAR motion delta，并把 localization/path bridge 接到真实 Nav2 path generation / route execution readback。若 CEO 能提供 O5 production evidence，则切回 O5 external production proof；否则不要继续消费 O5 support-only surface，也不要重复 historical manual gate intake。
