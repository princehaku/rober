# Hardware Worker Report

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

## 实际改动文件

- [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py)
- [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py)
- [`/Users/m1/apps/rober/docs/hardware/wave_rover_motion_map_hil_material_bundle.md`](/Users/m1/apps/rober/docs/hardware/wave_rover_motion_map_hil_material_bundle.md)
- [`/Users/m1/apps/rober/sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/tech-done.md`](/Users/m1/apps/rober/sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/tech-done.md)

## 实现内容

- 把 2026-06-11 manual HIL gate current evidence 接入现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`。
- 新增安全字段：manual gate blocked、missing fields、stop forwarded、manual local reject、remote manual not called、`T=130 -> T1001`、operator material-only。
- 保持所有顶层危险成功字段为 `false`，并对 remote manual 调用、核心 artifact 缺失、delivery claim 泄漏和 unsafe value 做 fail-closed。

## 验证命令结果

- `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py`
  - 通过。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'`
  - `Ran 33 tests in 0.246s`，`OK`。
- `PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle`
  - exit `0`。
  - 关键字段：`manual_hil_gate_current_evidence_material_present=true`、`manual_hil_gate_status=blocked`、`manual_gate_t1001_observed_count=2`、`proxy_remote_base_manual_not_called_by_local_reject=true`。
- `git diff --check -- ...`
  - 通过。

## 失败定位

- 本轮无首轮失败，无需返工。

## 未验证项 / 风险 / 下一步

- 未验证真实 current live HIL、真实非 stop 点动、轮向、IMU/battery 标定、same-run path generation success、Nav2 route execution success。
- 证据边界是历史上位机 / PC proxy software proof intake，不是现场通过证据。
- 下一步应采 current same-run 短动与 HIL acceptance 材料，再决定是否允许现场 controlled jog。
