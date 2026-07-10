# O1 Motion Map HIL Material Bundle Tech Done

## 实际改动

- 新增 [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py)，实现 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`：
  - 默认读取 `2026.06.22_01-35_motion_map_runtime_probe` 的 10 份历史现场材料；
  - 只消费 allowlist 字段并输出脱敏摘要；
  - 固定 `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`；
  - 固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`；
  - 对 core artifact 缺失、scan delta / operator claim mismatch、map/pixel review mismatch、dangerous true、unsafe consumed value 做 fail-closed。
- 新增 [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py)，覆盖：
  - positive historical run ready；
  - 正例不泄露 `source_base_url`、endpoint、`/root/...` 等 runtime 上下文；
  - missing feedback sample blocked；
  - feedback `all_samples_observed_t1001=false` blocked；
  - scan delta / operator claim mismatch blocked；
  - operator required true / required false 字段 blocked；
  - map / pixel review mismatch blocked；
  - dangerous true 与 unsafe consumed value blocked；
  - first jog `confirm_hil_checklist=false` blocked；
  - CLI 默认正例与 override 负例退出码。
- 新增 [`/Users/m1/apps/rober/docs/hardware/wave_rover_motion_map_hil_material_bundle.md`](/Users/m1/apps/rober/docs/hardware/wave_rover_motion_map_hil_material_bundle.md)，记录 vendor 来源、合同边界、fail-closed 规则和 CLI smoke。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py onboard/scripts/*.py`
  - 结果：通过，无输出。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'`
  - 首轮失败：`unsafe summary leakage detected` 把输出字段名 `run_token` 误判成敏感 `token`，同时 `operator structured_hil_claims.scan_delta_ref` 的 `/root/...` 原始路径本应只投影 run token，不该让正例 blocked。
  - 本轮返工首轮失败：`confirm_hil_checklist=false` 已进入 `blocked_reasons`，但 `first_jog_command_present` 仍然为 `true`。修复为 first jog 只有在 `confirm_hil_checklist=true` 且 `hil_checklist_gate_status=manual_allowed` 时才算 present。
  - 修复后结果：`Ran 10 tests in 0.017s OK`。
- positive CLI/module smoke
  - 命令：`PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle`
  - 结果：exit `0`，`status=motion_map_hil_material_bundle_ready_not_hil_pass`，`same_run_material_present=true`，`map_output_present=true`，`map_navigation_ready=false`，固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- negative CLI/module smoke
  - 命令：覆盖 `12_pc_feedback_samples_after_scan_delta_jog.json` 的 `sample_key_values.all_samples_observed_t1001='false'` 后执行 `--feedback-samples-json /tmp/.../bad-feedback.json`
  - 结果：exit `4`，`status=blocked_invalid_motion_map_hil_material_bundle`，`blocked_reasons=["feedback_all_samples_not_t1001"]`，固定 false 字段保持不变。
- `git diff --check -- onboard/src/ros2_trashbot_hardware onboard/scripts docs/hardware sprints/2026.07.10_18-24_o1_motion_map_hil_material_bundle`
  - 结果：通过，无输出。

## 剩余风险

- 本轮只证明历史 motion + map 现场材料已经被当前软件安全 intake，不证明 current live HIL。
- 当前两个 pixel review 都是 `has_free_cells=false`，因此 bundle 不能证明 map navigation ready。
- 仍缺 current same-run `feedback_T1001.log`、motion command record、operator / external observation、HIL acceptance record 和可导航 free-cell map。
