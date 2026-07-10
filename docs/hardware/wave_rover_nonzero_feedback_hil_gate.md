# WAVE ROVER Nonzero Feedback HIL Gate

## Vendor sources

本轮 O1 gate 只采用以下本地资料，不凭记忆补协议：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/hardware/wave_rover_json_bridge.md`

已采用的事实：

- WAVE ROVER 上下位机链路是 UART newline-delimited JSON。
- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO=1001`。
- 项目 parser 只承认 `T=1001` 且要求同帧存在 `L/R/r/p/y/v`。
- `base_ctrl.py` 的串口读取方式是一行一帧 JSON。

## Scope

`ros2_trashbot_hardware.wave_rover_nonzero_feedback_gate` 是纯 Python、离线、fail-closed 的 software proof gate：

- 读取 `feedback_T1001.log` 或 `--feedback-sample-json`。
- 复用 `wave_rover_feedback.py` 的 parser，不重复解析 vendor 字段。
- 只输出结构化 JSON summary，不打开串口、不 import ROS2 node、不发送控制命令。
- 固定输出：
  - `evidence_boundary=software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only`
  - `source=software_proof`
  - `hil_pass=false`
  - `safe_to_control=false`

## Gate behavior

本 gate 至少输出四类事实：

1. 是否读到合法 `T=1001`。
2. 是否看到同一帧 `L/R` 同时非零。
3. `L/R` 的符号模式摘要，例如 `both_positive`、`both_negative`、`left_positive_right_negative`。
4. 当前仍缺哪些真实 HIL 材料。

fail-closed 规则：

- 坏 JSON、缺字段、非 object、非法 `T=1001` payload 都记为 blocked 或 invalid。
- 非 `T=1001` 行只记为 ignored，不会抬高 gate。
- 只要同一输入里出现任意 invalid feedback line，顶层 `status` 就必须 blocked/invalid，CLI 也必须返回非 0；即使另一个样本里已经看到 `L/R` 非零，`counts`、`direction_summary`、`latest_nonzero_pair` 也只能作为诊断信息保留。
- 即使 mock 中观测到 `L/R` 非零，顶层仍保持 `hil_pass=false`、`safe_to_control=false`。
- `direction_summary` 只是 `L/R` 符号模式摘要，不等于真实车体前进/后退/转向已在现场验证。

## Remaining live HIL materials

本 gate 不能代替真实上车证据。真实履约仍需至少补齐：

- 同一 run 的真实 `feedback_T1001.log`。
- 同一 run 的 motion command record。
- 同一 run 的 operator report 或外部运动观察材料。
- 同一 run 的 HIL acceptance record。

没有这些材料时，本 gate 只能证明“软件能保守地读、判、挡”，不能证明真实 WAVE ROVER nonzero L/R，也不能证明 HIL pass。
