# Operator Gateway WAVE ROVER Hardware Diagnostics Modularization

## sprint_type

micro

## 实际改动

- 新增 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_wave_rover_hardware.py`，承接 WAVE ROVER feedback replay、WAVE ROVER HIL packet intake/review/execution pack/collection drill、hardware baseline review、hardware baseline source alignment 的 schema/gate 常量、默认 blocked summary、`not_proven` helper、source contract、unsafe/disabled-action/same-evidence-ref helper 和 summarize 函数。
- 更新 `operator_gateway_diagnostics.py` 为兼容 facade，继续 re-export 原有 `WAVE_ROVER_FEEDBACK_REPLAY_*`、`WAVE_ROVER_HIL_PACKET_*`、`HARDWARE_BASELINE_REVIEW_*`、`HARDWARE_BASELINE_SOURCE_ALIGNMENT_*` 和 `summarize_*` 名称；`build_diagnostics_payload` 调用点、payload key、alias 和环境变量入口保持不变。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录新的 WAVE ROVER hardware diagnostics 模块边界，并声明本轮为结构拆分，不改变 schema/gate/payload/alias/not_proven/unsafe-control/disabled-action/same-evidence-ref 语义。

## 已读 vendor 来源

- `AGENTS.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/README.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

## 硬件结论边界

本轮没有新增或修改硬件结论。代码改动只移动 diagnostics metadata 组织结构，不新增或修改 UART 路径、波特率、JSON 指令、速度映射、feedback 字段、电压、引脚、底盘协议、固件、机械尺寸或真实 HIL 验收结论。WAVE ROVER/UART/odom/IMU/battery/HIL 仍保持 `not_proven`，真实上车证据仍需单独采集。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 7.067s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无输出。
- `cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_wave_rover_hardware.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_28-29_operator-gateway-wave-rover-hardware-modularization/tech-done.md`
  - 结果：通过，无输出。

## 剩余风险

- 本轮验证为软件单测、Python 编译和 diff 空白检查；没有连接真实 WAVE ROVER、Orange Pi UART、底盘 ESP32、odom/IMU/battery topic 或 HIL 采集包。
- 当前工作区存在其他未关联 dirty/untracked sprint 和 diagnostics 文件，本轮未回滚、未清理、未纳入验证结论。
