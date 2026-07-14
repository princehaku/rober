# O1 Same-Session PC Command Material Tech Done

## sprint_type: epic

## 实际改动

- 在 `wave_rover_motion_map_hil_material_bundle.py` 新增 `02_pc_first_jog_samesession_timeoutfix.json` 与 `03_base_status_after_pc_jog.json` 的默认输入路径。
- 新增 `same_session_pc_command_material` parser，只提取 allowlisted 的 PC first-jog command、motion-window nonzero wheel material 与 after-jog `T=130 -> T=1001` 零速 readback 摘要。
- bundle 只输出 `same_session_pc_command_*` 前缀字段，不输出裸名 `wheel_feedback_lr_nonzero_proven=true`，并继续固定顶层 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`。
- 新增测试覆盖：正例合同输出、泄露围栏继续有效、after-jog 非零 readback 篡改时 fail-closed。
- 更新 `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`，补充 vendor 来源、同会话 PC command 合同和 fail-closed 规则。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py`
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'`
- `PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle`
- `rg -n "same_session_pc_command|same_session_hil_acceptance|blocked_missing_current_live_acceptance" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.11_02-34_o1_same_session_pc_command_material`
- `git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py docs/hardware/wave_rover_motion_map_hil_material_bundle.md sprints/2026.07.11_02-34_o1_same_session_pc_command_material`

实际结果：

- `python3 -m py_compile ...`：通过。
- `python3 -m unittest discover ...`：`Ran 36 tests in 0.289s`，`OK`。
- CLI：exit `0`，输出 `status=motion_map_hil_material_bundle_ready_not_hil_pass`、`same_session_pc_command_material_present=true`、`same_session_pc_command_material_status=same_session_pc_command_material_ready_not_hil_pass`、`same_session_pc_command_latest_nonzero_pair.left_speed=20.0/right_speed=20.0`、`same_session_pc_command_after_jog_latest_pair.left_speed=0.0/right_speed=0.0`、`same_session_hil_acceptance_status=blocked_missing_current_live_acceptance`。
- anchor `rg`：命中代码、文档和 sprint 留档中的 `same_session_pc_command*`、`same_session_hil_acceptance*` 锚点。
- scoped `git diff --check`：通过。

## 剩余风险

- 证据边界仍是 historical same-session software proof intake，不证明 current live HIL、safe-to-control、delivery success 或 current live route execution success。
- `03_base_status_after_pc_jog.json` 的 `feedback_samples_latest.freshness.status=stale` 只能作为 readback context，不能当作 current live acceptance。
- O1 本轮只能算 evidence envelope additive delta；是否上调 OKR 仍取决于是否认可消费 `02/03` 为新的 same-session mission material。
