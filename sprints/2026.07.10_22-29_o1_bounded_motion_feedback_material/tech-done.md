# O1 Bounded Motion Feedback Material Tech Done

## sprint_type

sprint_type: epic

## 已读资料和 vendor 来源

- 已读 `AGENTS.md`、`OKR.md`、本 sprint `pre_start.md`、`prd.md`、`tech-plan.md`。
- 已读 `docs/vendor/VENDOR_INDEX.md`。
- 已读 WAVE ROVER 本地 vendor 文件：
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

采用的硬件事实：WAVE ROVER 上下位机链路是 UART JSON line；`T=130` 是 base feedback request；`T=1001` 是 base feedback material 类型；本轮不新增真实控制动作、不改串口、速度映射或 launch 默认值。

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
  - 在 `DEFAULT_PATHS` 增加 2026-06-10 bounded motion / T1001 / IMU-battery / odom readback required artifacts 和 optional diagnostic sweep。
  - 新增 bounded motion summary、ROS sample text、PC readback summary、`base_feedback_samples_latest` 和 wheel diagnostic sweep parser。
  - 输出 additive `bounded_motion_feedback_material` 字段：`bounded_motion_feedback_material_present=true`、`feedback_motion_summary_present=true`、`base_feedback_samples_latest_present=true`、`bounded_motion_command_observed=true`、`bounded_motion_duration_lte_0_3s=true`、`bounded_motion_stop_observed=true`、`t1001_feedback_before_after_observed=true`、`t1001_feedback_sample_count=2`、`t1001_observed_count=2`、`odom_readback_sample_present=true`、`imu_sample_present=true`、`battery_sample_present=true`。
  - 固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`、`bounded_motion_lr_nonzero_proven=false`、`wheel_direction_proven=false`、`imu_battery_calibration_proven=false`。
  - 将 `base_feedback_samples_latest.latest_result.sends_commands=true` 仅解释为 `T=130` feedback request context，并保持 `sends_motion_commands=false`。
  - optional diagnostic sweep 仅输出 `wheel_feedback_sweep_all_nonzero_lr_count_zero=true`；若 sweep 被篡改出非零 L/R，会 blocked。
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
  - 扩展正例断言，覆盖 bounded motion / T1001 / IMU-battery / odom readback 字段。
  - 新增 duration 超界、T130 request 误升格、dangerous true、文本泄露和 diagnostic 非零 L/R fail-closed 测试。
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
  - 记录 2026-06-10 bounded motion feedback material 的输入、合同字段、fail-closed 规则和 proof boundary。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py`：通过。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'`：通过，`Ran 29 tests in 0.173s OK`。
- `PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle`：exit 0；输出 `status=motion_map_hil_material_bundle_ready_not_hil_pass`、`bounded_motion_feedback_material_present=true`、`base_feedback_samples_latest_present=true`、`blocked_reasons=[]`，安全字段保持 false。
- `rg -n "bounded_motion_feedback|bounded_motion_feedback_material|feedback_motion_summary|base_feedback_samples_latest|hil_pass=false|safe_to_control=false|delivery_success=false" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material`：通过，命中代码、测试、硬件文档和 sprint 留档锚点。
- `git diff --check -- onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material`：通过，无 whitespace error。

## 失败定位和修复

- 首轮新增测试把历史字段名 `run_token` 误判成敏感 token 泄露；已修正为只检查真实敏感样例 `token-secret`，实现无需改动。

## 证据边界和剩余风险

- 本轮 proof boundary 仍为 `software_proof_o1_motion_map_hil_material_bundle_only`。
- 这是 historical upper-computer software proof，不是 current live HIL。
- T1001 readback 只证明 feedback material observed，不证明 bounded-run L/R 非零、wheel direction 或 HIL pass。
- `/odom`、`/imu/data`、`/battery` 只证明 sample/readback present，不证明 dynamic odom、IMU/battery calibration、Nav2 route execution 或 delivery success。
- 仍缺 current live same-run `feedback_T1001.log`、motion command record、operator/external observation、HIL acceptance、wheel direction confirmation、IMU/battery calibration record 和 live Nav2 route execution result。
