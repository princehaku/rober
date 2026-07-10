# O1 Manual HIL Gate Current Evidence Intake Tech Done

## sprint_type

sprint_type: epic

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

采用事实：

- `base_ctrl.py` 与 `json_cmd.h` 说明上下位机链路为 UTF-8 JSON 行协议。
- `json_cmd.h` / `uart_ctrl.h` 说明 `T=130` 是 base feedback request，`T=1001` 是底盘反馈。
- 本轮只消费历史 real-board / PC proxy 材料，不发送 `T=1`、`T=13`、`/api/base/manual` 或串口写运动命令。

## 实际改动

1. 扩展 [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py)
   - 新增 2026-06-11 manual HIL gate artifacts 默认路径。
   - 新增 additive section `manual_hil_gate_current_evidence_material`。
   - 新增 fail-closed 解析：manual gate blocked、missing fields、stop forwarded、manual local reject、remote `/api/base/manual` not called、`T=130 -> T1001 x2`、operator structured report material-only。
   - 固定顶层 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`。
2. 扩展 [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py)
   - 新增 manual gate 正例回归。
   - 新增 remote `/api/base/manual` 被调用时 blocked。
   - 新增缺核心 artifact 时 blocked。
   - 新增 operator 顶层 `delivery_success` 泄漏与 unsafe value 时 blocked 且不回显。
3. 更新 [`/Users/m1/apps/rober/docs/hardware/wave_rover_motion_map_hil_material_bundle.md`](/Users/m1/apps/rober/docs/hardware/wave_rover_motion_map_hil_material_bundle.md)
   - 补充 manual HIL gate 输入材料、输出字段和 fail-closed 规则。

## 已证实的硬件/材料结论

- `manual_hil_gate_current_evidence_material_present=true`
- `manual_hil_gate_status=blocked`
- `manual_hil_gate_missing_fields=["external_video_recorded","visible_content_proven","wheel_feedback_lr_nonzero_proven","physical_motion_lidar_delta_proven"]`
- `visible_content_proven_blocks_motion=true`
- `manual_nonzero_policy=do_not_send_nonzero_expect_pc_local_reject`
- `stop_safety_smoke_forwarded=true`
- `manual_nonstop_local_reject_present=true`
- `manual_nonstop_remote_base_manual_called=false`
- `proxy_remote_base_manual_not_called_by_local_reject=true`
- `manual_gate_t1001_observed_count=2`
- `manual_gate_all_samples_observed_t1001=true`
- `manual_gate_feedback_request_t130_observed=true`
- `operator_structured_report_material_only=true`
- `operator_structured_report_status=ready_for_execution`
- `operator_structured_delivery_claim_material_only=true`
- `manual_hil_gate_ready_not_hil_pass=true`

## 验证结果

1. `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py`
   - 结果：通过。
2. `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'`
   - 结果：`Ran 33 tests in 0.246s`，`OK`。
3. `PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle`
   - 结果：CLI exit `0`。
   - 关键输出：`status=motion_map_hil_material_bundle_ready_not_hil_pass`、`manual_hil_gate_current_evidence_material_present=true`、`manual_hil_gate_status=blocked`、`manual_gate_t1001_observed_count=2`、`proxy_remote_base_manual_not_called_by_local_reject=true`。
4. `rg -n "manual_hil_gate_current_evidence|manual_hil_gate_ready_not_hil_pass|remote_base_manual_not_called|operator_structured_report" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake`
   - 结果：命中新代码、文档和 sprint 计划锚点。
5. `git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py docs/hardware/wave_rover_motion_map_hil_material_bundle.md sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake`
   - 结果：通过。

## 失败定位

- 首轮验收无失败；`py_compile`、单测、CLI、anchor `rg` 和 scoped `git diff --check` 均一次通过。

## 证据边界与剩余风险

- 本轮证据边界仍是 `software_proof_o1_motion_map_hil_material_bundle_only`。
- 本轮只证明历史 real-board / PC proxy manual gate 材料已被当前软件安全 intake，不证明 current live HIL pass、safe-to-control、delivery success、wheel direction、IMU/battery calibration、same-run path generation success、Nav2 route execution success 或真实 production cloud。
- `manual_hil_gate_status=blocked` 说明现场仍缺 `external_video_recorded`、`visible_content_proven`、`wheel_feedback_lr_nonzero_proven`、`physical_motion_lidar_delta_proven`。
- 下一步履约动作应转向 current same-run 现场短动材料采集：`feedback_T1001.log`、motion command record、operator/external motion observation、HIL acceptance record。
