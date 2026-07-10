# O1 Manual HIL Gate Current Evidence Intake Side-by-Side Check

## 对照结论

- 需求要求的是把 2026-06-11 的真实 PC proxy / real-board manual gate 只读材料接入现有 O1 bundle，并保持 fail-closed，不宣称 HIL pass。
- Hardware owner 实际交付与要求一致：`manual_hil_gate_current_evidence_material` 已进入 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，并把 stop 转发、non-stop local reject、remote `/api/base/manual` 未调用、`T=130 -> T1001 x2`、operator material-only claim 都写成可复验摘要。
- Product 验收通过，但结论保持保守：`manual_hil_gate_status=blocked`，`hil_pass=false`，`safe_to_control=false`，`delivery_success=false`，不把 historical material intake 误记成 current live HIL。

## 用户价值和产品北极星

用户价值是让现场人员在下一次短动 HIL 前，不必手翻多个 JSON 才知道 stop 路径是否可用、non-stop manual 为什么仍被拒绝、当前到底缺哪些现场材料。产品北极星不变：普通手机用户可安全、可验证地完成垃圾送达，而不是只做“看起来 ready”的材料包装。

## OKR 映射和方向判断

- O1：继续，约 `~91% -> ~92%`。理由是本轮消费了不同于上一轮 bounded-motion 的 historical real-board / PC proxy manual HIL gate material delta，并把安全/fail-closed 合同与测试落地。
- O5：继续暂停计分，保持约 `~85%`。理由是 `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已明确 `okr_credit_allowed=false`，当前仍无真实 external production evidence。
- O6/O7：保持约 `~92%`。本轮没有新增 O6 archive/readback 或 O7 UI/consumer 交付。

方向判断：继续 O1，但下一轮必须切到 current same-run 现场短动证据，不再重复 historical gate intake。

## 核心抓手与验收口径对照

- 已命中 `manual_hil_gate_current_evidence_material_present=true`
- 已命中 `manual_hil_gate_status=blocked`
- 已命中 `manual_hil_gate_missing_fields=[external_video_recorded, visible_content_proven, wheel_feedback_lr_nonzero_proven, physical_motion_lidar_delta_proven]`
- 已命中 `stop_safety_smoke_forwarded=true`
- 已命中 `manual_nonstop_local_reject_present=true`
- 已命中 `manual_nonstop_remote_base_manual_called=false`
- 已命中 `proxy_remote_base_manual_not_called_by_local_reject=true`
- 已命中 `manual_gate_t1001_observed_count=2`
- 已命中 `operator_structured_delivery_claim_material_only=true`
- 安全字段继续固定：`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`

## 对应责任 Engineer

- 主责 Engineer：`rober-hardware-engineer`
- Product closeout：`product-okr-owner`

## 验证结果

Hardware `tech-done.md` 已记录并通过：

- `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py`
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'` -> `Ran 33 tests in 0.246s OK`
- `PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle` -> exit `0`

Product closeout 补充验证见 `artifacts/product_worker_report.md`。

## 风险、阻塞和需要补齐的证据链

- 当前仍缺 `external_video_recorded`
- 当前仍缺 `visible_content_proven`
- 当前仍缺 `wheel_feedback_lr_nonzero_proven`
- 当前仍缺 `physical_motion_lidar_delta_proven`
- `manual_hil_gate_status=blocked` 说明现场还不能把这份材料当成 HIL pass 或 safe-to-control

## 已完成 KR 的历史记录位置、证据来源和剩余风险

- 本轮无已完成 KR，不归档 KR
- 证据来源：
  - `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/tech-done.md`
  - `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/artifacts/hardware_worker_report.md`
  - `sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material/final.md`
  - `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md`
- 剩余风险：proof boundary 仍是 `software_proof_o1_motion_map_hil_material_bundle_only`，不是 current live HIL、不是 safe-to-control、不是 delivery success

## 需要创建或更新的 sprint 文档

- 本文件 `side2side_check.md`
- `final.md`
- `artifacts/product_worker_report.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
