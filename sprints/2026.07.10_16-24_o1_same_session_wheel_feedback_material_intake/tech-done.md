# O1 Same-session WAVE ROVER Wheel Feedback Material Intake Tech Done

## sprint_type

sprint_type: epic

## 已读资料和 vendor 来源

本轮已读取：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/pre_start.md`
- `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/prd.md`
- `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/tech-plan.md`
- `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json`
- `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/tech-done.md`
- `sprints/2026.06.27_00-42_first_jog_motion_feedback_window/tech-done.md`

采用的 vendor 事实：

- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO=1001`、`CMD_SPEED_CTRL=1`、`CMD_BASE_FEEDBACK=130`。
- `uart_ctrl.h` 以换行结束 JSON 后调用 `deserializeJson`，并把 `T=1`、`T=130` 分发到底盘速度和反馈函数。
- `ugv_rpi/base_ctrl.py` 使用 `json.dumps(data) + '\n'` 写 UART，并用 UTF-8 JSON line 读取反馈。
- `ugv_rpi/config.yaml` 保留 vendor 应用命令 ID、速度配置和反馈配置，本轮不把串口路径或 baudrate 写入输出摘要。

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_same_session_wheel_feedback_material.py`
  - 新增 `trashbot.wave_rover_same_session_wheel_feedback_material.v1` material intake。
  - 只消费历史上位机 artifact 的 `serial_motion_transaction` 阶段摘要：motion `T=1`、motion window `T=130`、motion window `T=1001 L/R` 同帧非零、stop `T=1 L/R=0/0`、after-stop `T=130`、after-stop `T=1001 L/R=0/0`。
  - 输出 `same_session_wheel_feedback_material_ready_not_delivery_proof` 或 fail-closed blocked 摘要，固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
  - 输出层安全检查禁止回显 URL、完整绝对路径、串口设备名、baudrate、token、password、secret、traceback 和 raw payload。
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_same_session_wheel_feedback_material.py`
  - 覆盖 positive historical artifact、missing nonzero、missing stop-zero、dangerous true + unsafe text、bad schema/shape、nonzero outside motion window、CLI ready/block、bad JSON。
- `onboard/src/ros2_trashbot_hardware/setup.py`
  - 新增 `wave_rover_same_session_wheel_feedback_material` console script。
- `docs/hardware/wave_rover_same_session_wheel_feedback_material.md`
  - 新增合同、fail-closed 规则、CLI smoke 和 next evidence 文档。
- `docs/hardware/wave_rover_json_bridge.md`
  - 追加 O1 same-session material intake 边界说明。
- `sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/tech-done.md`
  - 记录本轮实现、验证和剩余风险。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_hardware/**/*.py`
  - 通过，exit code 0。
- `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*wave*rover*.py'`
  - 通过：`Ran 18 tests in 0.013s`，`OK`。
- Positive CLI smoke：
  - 命令：`PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_same_session_wheel_feedback_material sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json`
  - 结果：exit code 0，`status=same_session_wheel_feedback_material_ready_not_delivery_proof`，`latest_nonzero_pair.left_speed=61.0`，`latest_nonzero_pair.right_speed=61.0`，`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- Unsafe/dangerous CLI smoke：
  - 输入：临时 artifact 将 `safe_to_control=true`。
  - 结果：exit code 4，`status=blocked_invalid_same_session_wheel_feedback_material`，`blocked_reasons=["dangerous_true_safe_to_control"]`，输出仍固定 `safe_to_control=false`。
- `git diff --check -- onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake`
  - 通过，exit code 0。

## 失败定位

本轮验证未发现失败项。实现过程中注意到 worktree 已有未提交的 O1 nonzero feedback gate 相关文件和 `setup.py` 修改；本轮没有回滚或格式化这些既有改动，只在允许范围内追加 same-session material intake。

## 剩余风险

- 本轮消费的是历史真实上位机 same-session artifact，不是 current live HIL run。
- `T=1001 L/R=61/61` 只证明历史同一手控会话内 wheel feedback material 存在，不能证明当前硬件 safe-to-control、Nav2 route execution、delivery success 或 production cloud。
- O1 下一步仍需要新的同 run `feedback_T1001.log`、motion command record、operator / external motion observation 和 HIL acceptance record。

