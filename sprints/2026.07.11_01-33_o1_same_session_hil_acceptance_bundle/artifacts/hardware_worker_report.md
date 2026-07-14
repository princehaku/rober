# Hardware Worker Report

## Run

- Role: `robot-hardware-engineer`
- Sprint: `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/`
- Run time: `2026-07-11 01:44:50 CST`

## Scope

只改动本轮允许范围：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/tech-done.md`
- `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/artifacts/hardware_worker_report.md`

未修改 `OKR.md`、`docs/process/okr_progress_log.md`、O6/O7 workstation、relay 或其他范围外文件。

## Vendor Sources Read

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

结论：WAVE ROVER UART 使用 UTF-8 newline-delimited JSON；`T=1` 是 L/R 速度命令，`T=130` 请求底盘反馈，`T=1001` 是底盘反馈并含 L/R 轮速材料。当前 Orange Pi 真实串口路径仍需上车确认，本轮不新增串口默认值。

## Implementation

新增 same-session wheel feedback additive parser：

- 默认读取 `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json`。
- 只消费 allowlisted material，不输出 `/dev/tty*`、`115200`、endpoint、URL、token、traceback、raw frames 或长 raw 内容。
- 输出 `same_session_wheel_feedback_*` 前缀字段，避免裸名 `wheel_feedback_lr_nonzero_proven=true` 被误读成顶层 HIL/safety success。
- 输出 `same_session_hil_acceptance_status=blocked_missing_current_live_acceptance`，明确缺 current live acceptance material。
- 保持顶层 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`。

## Verification

- `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py`
  - exit code 0，无输出。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'`
  - exit code 0；`Ran 35 tests in 0.261s`、`OK`。
- `PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle`
  - exit code 0；输出 ready bundle。
  - same-session 摘要：`left_speed=61.0`、`right_speed=61.0`、`sign_pattern=both_positive`、`same_session_hil_acceptance_status=blocked_missing_current_live_acceptance`。
- `rg -n "same_session_wheel_feedback|same_session_hil_acceptance|blocked_missing_current_live_acceptance" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle`
  - exit code 0。
- `git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py docs/hardware/wave_rover_motion_map_hil_material_bundle.md sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle`
  - exit code 0，无输出。

## Failure Analysis

无验证失败。未遇到需要越界修改的依赖问题。

## Remaining Risk

- 当前证据是 historical same-session upper-computer material，不是 current live rerun。
- 不证明 current live HIL pass、safe-to-control、delivery success、wheel direction、IMU/battery calibration 或 Nav2 route execution success。
- O1 不应因本轮合同接线重复上调；下一轮必须采 current live same-run HIL acceptance bundle。
