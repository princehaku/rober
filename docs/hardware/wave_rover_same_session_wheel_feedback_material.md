# WAVE ROVER Same-session Wheel Feedback Material Intake

## Vendor sources

本 material intake 采用以下本地资料，不从记忆推断协议字段：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

采用的硬件事实：

- WAVE ROVER UART 使用 UTF-8 JSON line，每帧以 `\n` 结束。
- `T=1` 是左右轮速度命令，字段为 `L/R`。
- `T=130` 是一次性底盘反馈请求。
- `T=1001` 是底盘反馈帧，`L/R` 是本轮只读摘要所消费的 wheel feedback 字段。

## Contract

新增合同：

- `schema=trashbot.wave_rover_same_session_wheel_feedback_material.v1`
- `proof_scope=software_proof_o1_same_session_wheel_feedback_material_intake_only`
- ready status: `same_session_wheel_feedback_material_ready_not_delivery_proof`

输入材料是历史真实上位机 artifact：

- `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json`

intake 只消费 `serial_motion_transaction` 的阶段摘要：

- motion command: `T=1` 且 `L/R` 至少一个非零。
- motion feedback request: `T=130`。
- motion window feedback: `T=1001` 且同一帧 `L/R` 都非零。
- stop command: `T=1 L/R=0/0`。
- after-stop feedback request: `T=130`。
- after-stop feedback: `T=1001 L/R=0/0`。

输出只包含安全摘要：布尔状态、计数、最后一个非零 `L/R` pair、blocked reasons、next required evidence 和 vendor/source refs。输出不得包含 raw artifact payload、完整绝对路径、URL、token、base64、traceback、串口设备名、baudrate、endpoint 或 compact frames。

## Fail-closed rules

下列任一情况必须 blocked：

- artifact 不是 JSON object 或 JSON 解析失败。
- top-level schema 不是 `trashbot.upper_robot_api.v1.base_manual_result`。
- `source` 明确声明为非 upper robot API / historical same-session 来源。
- `hil_pass`、`safe_to_control`、`delivery_success`、`primary_actions_enabled` 任一输入为 `true`。
- 输入包含 token/password/secret/authorization 类 key，或 URL、绝对用户路径、traceback、疑似长 base64 文本。
- 缺少 `serial_motion_transaction`。
- 缺少运动命令、运动中 `T=130`、运动窗口 `T=1001` 非零 pair、stop 命令、stop 后 `T=130` 或 stop 后 `T=1001 L/R=0/0`。
- 非零 `L/R` 只出现在 stop 后或其他非 motion window 位置。

blocked 输出仍固定：

- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## CLI smoke

本地复验示例：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_same_session_wheel_feedback_material sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json
```

ready 输出只证明历史 same-session wheel feedback material 已被安全接入。它不证明 current live HIL、硬件 safe-to-control、Nav2 route execution、delivery success 或 production cloud。

## Next evidence required

要推进 O1 真实现场履约，仍需新的同 run 材料：

- current live same-run `feedback_T1001.log`
- current live motion command record
- operator / external motion observation
- HIL acceptance record

