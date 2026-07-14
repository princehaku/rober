# O1 Same-Session HIL Acceptance Bundle Tech Done

## sprint_type

sprint_type: epic

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
  - 在 `trashbot.wave_rover_motion_map_hil_material_bundle.v1` 中新增 `same_session_wheel_feedback_json` 默认输入。
  - 新增 same-session wheel feedback additive parser，只消费 allowlisted 字段，不回显串口、baudrate、endpoint、URL、token、traceback、raw frames 或长 raw 内容。
  - 输出 `same_session_wheel_feedback_material_status=same_session_wheel_feedback_material_ready_not_hil_pass`、`same_session_wheel_feedback_latest_nonzero_pair.left_speed=61.0/right_speed=61.0/sign_pattern=both_positive`。
  - 输出 `same_session_hil_acceptance_status=blocked_missing_current_live_acceptance` 和 current live acceptance 缺口列表。
  - 保持顶层 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`。
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
  - 新增 positive assertions 覆盖 same-session additive fields。
  - 新增 dangerous true fail-closed 测试。
  - 新增 unsafe consumed pair source 不泄露测试。
  - 扩展 runtime context 泄露断言，覆盖 `serial_motion_transaction`、`compact_frames` 和 `/api/base`。
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
  - 同步 vendor 来源、same-session 输入、输出字段、fail-closed 规则和 CLI 覆盖示例。
- `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/tech-done.md`
  - 记录本轮实现、验证、风险和 OKR 判断。
- `sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle/artifacts/hardware_worker_report.md`
  - 记录 Hardware worker 执行报告。

## 已读资料和 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

采用的硬件事实：

- UART 链路按 UTF-8 JSON line，以 `\n` 分帧。
- `T=1` 是左右轮速度命令，字段为 `L/R`。
- `T=130` 是一次性底盘反馈请求。
- `T=1001` 是底盘反馈，`ugv_advance.h` 的 `baseInfoFeedback()` 输出 `L/R/r/p/y/v`。
- Vendor Raspberry Pi 默认串口/波特率只作为 vendor 事实来源，本轮 bundle 不输出 `/dev/tty*` 或 `115200`。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py`
  - exit code 0，无输出。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'`
  - exit code 0。
  - 关键输出：`Ran 35 tests in 0.261s`、`OK`。
- `PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle`
  - exit code 0。
  - 关键输出：`status=motion_map_hil_material_bundle_ready_not_hil_pass`、`same_session_wheel_feedback_material_present=true`、`same_session_wheel_feedback_material_status=same_session_wheel_feedback_material_ready_not_hil_pass`、`same_session_wheel_feedback_latest_nonzero_pair.left_speed=61.0`、`same_session_wheel_feedback_latest_nonzero_pair.right_speed=61.0`、`same_session_hil_acceptance_status=blocked_missing_current_live_acceptance`。
  - 顶层仍为 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`。
- `rg -n "same_session_wheel_feedback|same_session_hil_acceptance|blocked_missing_current_live_acceptance" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle`
  - exit code 0。
  - 命中代码、测试、硬件文档和本 sprint 计划/留档。
- `git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py docs/hardware/wave_rover_motion_map_hil_material_bundle.md sprints/2026.07.11_01-33_o1_same_session_hil_acceptance_bundle`
  - exit code 0，无输出。

## 失败定位

无验证失败。实现过程中没有发现需要修改范围外文件的问题。

## 剩余风险

- 该 artifact 是 historical same-session material，不是本轮 current live rerun。
- 不证明 current live HIL pass。
- 不证明真实 safe-to-control、真实 delivery success、轮速方向、IMU/battery calibration、Nav2 route execution success 或 current live map navigation readiness。
- 不应因为本轮合同接线重复上调 O1；下一步必须采 current live same-run `feedback_T1001.log`、motion command record、external video / LiDAR motion delta、operator observation 和 HIL acceptance record。

## O1 调整建议

不建议本轮上调 O1。理由：本轮消费的是已有 historical same-session material，并把它接入 composite HIL acceptance gap view；没有新增 current live artifact，也没有 current live HIL acceptance record。
