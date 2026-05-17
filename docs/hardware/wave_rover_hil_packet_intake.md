# WAVE ROVER HIL Packet Intake Gate

## Vendor sources

本 gate 的硬件事实只采用本地 vendor 资料：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

已证实的 vendor 结论：

- WAVE ROVER 上下位机链路是 UART newline-delimited JSON。
- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO 1001`，本 gate 的 feedback 文件只接受 `T=1001`。
- `uart_ctrl.h` 按 `T` 分发 JSON command，并包含 `CMD_BASE_FEEDBACK`、`CMD_BASE_FEEDBACK_FLOW`、`CMD_FEEDBACK_FLOW_INTERVAL` 等分支。
- `base_ctrl.py` 用 `json.loads(...readline...)` 读取一行 JSON，并用 `json.dumps(data) + '\n'` 发送命令。
- `config.yaml` 是 vendor upper-computer 的 command ID、feedback key 和 `feedback_interval` 配置参考。

这些来源只证明协议和配置出处，不证明本轮存在真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery` 或 `hil_pass`。

## Scope

`pc-tools/evidence/wave_rover_hil_packet_intake.py` 是 dependency-free PC gate：

- 只读取一个 packet directory。
- 必需文件为 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report.json` 或 `operator_hil_report.md`。
- 不打开 serial，不读取 `/dev/*`，不 import ROS2，不调用 ROS graph。
- 输出 `schema=trashbot.wave_rover_hil_packet_intake.v1`。
- 输出 `summary_schema=trashbot.wave_rover_hil_packet_intake_summary.v1`。
- 输出 `evidence_boundary=software_proof_docker_wave_rover_hil_packet_intake_gate`。
- 始终保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`same_evidence_ref_required=true`。

通过 synthetic fixture 时，`packet_status=pass` 只表示 packet contract 可解析且同一 `evidence_ref` 对齐；它仍然不是 `hil_pass`。

## Packet contract

`feedback_T1001.log`：

- 每个非空行必须是 JSON object。
- 支持直接 `{"T":1001,...}`。
- 支持 wrapper 字段 `feedback`、`payload`、`message` 内嵌 `T=1001`。
- 必须包含 `T,L,R,r,p,y,v`。
- 必须携带 safe `evidence_ref`。

`odom_once.jsonl`：

- 至少一条 JSON object。
- 必须携带 safe `evidence_ref`。
- 至少包含 `pose`、`twist`、`position`、`orientation`、`linear`、`angular` 之一。

`imu_once.jsonl`：

- 至少一条 JSON object。
- 必须携带 safe `evidence_ref`。
- 至少包含 `orientation`、`angular_velocity`、`linear_acceleration`、`rpy`、`yaw` 之一。

`battery_once.jsonl`：

- 至少一条 JSON object。
- 必须携带 safe `evidence_ref`。
- 至少包含 `voltage`、`percentage`、`power_supply_status`、`current` 之一。

`operator_hil_report`：

- 支持 `.json` 或简单 `key: value` 的 `.md`。
- 必须包含 `operator`、`run_timestamp`、`robot_id`、`serial_visibility_statement`、`stop_path_statement`、`result_boundary`。
- summary 只输出字段状态和安全边界，不回显完整 notes。

所有文件必须共享同一个 safe `evidence_ref`；命令行 `--evidence-ref` 存在时也必须一致。

## Fail-closed rules

以下情况必须 blocked：

- packet directory 缺失。
- 必需文件缺失或 `operator_hil_report.json` / `.md` 二者同时存在。
- JSON / JSONL / log malformed。
- `feedback_T1001.log` 缺少 `T=1001`。
- topic once 文件缺少最小字段。
- 任一文件缺少 safe `evidence_ref` 或 `evidence_ref` mismatch。
- operator report 缺失必需字段。
- 输入内容泄漏 unsafe local path、serial、baudrate、raw path、credential、checksum 或 traceback。
- 输入内容出现 `delivery_success=true`、`primary_actions_enabled=true` 或 `hil_pass` success claim。

失败时仍输出 `schema=trashbot.wave_rover_hil_packet_intake.v1` 与 `overall_status=blocked_not_proven`，方便 Robot diagnostics 和 mobile web 只读 fail-closed。

## Example

```bash
python3 pc-tools/evidence/wave_rover_hil_packet_intake.py \
  pc-tools/evidence/fixtures/wave_rover_hil_packet_intake/pass \
  --evidence-ref hil-packet-fixture-pass \
  --summary-output /tmp/wave_rover_hil_packet_intake_summary.json \
  --once-json
```

## Next required evidence

真实上车前仍需补齐：

- 真实 WAVE ROVER HIL run。
- 真实 `feedback_T1001.log`。
- 真实 `odom_once.jsonl`。
- 真实 `imu_once.jsonl`。
- 真实 `battery_once.jsonl`。
- 人工 `operator_hil_report`。
- 同一个 safe `evidence_ref` 绑定整包材料。

本 gate 只完成 `software_proof_docker_wave_rover_hil_packet_intake_gate`，不提升为真实 HIL、真实串口或 delivery success。
