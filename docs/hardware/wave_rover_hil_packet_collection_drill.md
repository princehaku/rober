# WAVE ROVER HIL Packet Collection Drill Gate

## Vendor sources

本 gate 的硬件事实只采用本地 vendor 资料：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

已证实的 vendor 结论：

- WAVE ROVER 上下位机链路是 UART newline-delimited JSON。
- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO 1001`，collection drill 的 `feedback_T1001.log` 只能对应 `T=1001` base feedback。
- `json_cmd.h` 定义 `CMD_SPEED_CTRL 1`、`CMD_ROS_CTRL 13`、`CMD_BASE_FEEDBACK 130`、`CMD_BASE_FEEDBACK_FLOW 131`、`CMD_FEEDBACK_FLOW_INTERVAL 142` 和 `CMD_UART_ECHO_MODE 143`。
- `uart_ctrl.h` 按 JSON 字段 `T` 分发命令，包含 base feedback、feedback flow、feedback interval 和 UART echo mode 分支。
- `base_ctrl.py` 使用 `json.loads(...readline...)` 读取一行 JSON，并使用 `json.dumps(data) + '\n'` 发送命令。
- `base_ctrl.py` 的 Raspberry Pi reference 使用 `/dev/ttyAMA0` at `115200`，但 Orange Pi 目标不能硬编码该路径；本 gate 也不会输出 serial device 或 baudrate。
- `config.yaml` 是 vendor upper-computer 的 command ID、feedback key、速度和 `feedback_interval` 配置参考。

这些来源只证明协议、命令编号和配置出处，不证明本轮存在真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 2D LiDAR/ToF、PR #5 reviewer resolution、`hil_pass` 或 delivery success。

## Scope

`pc-tools/evidence/wave_rover_hil_packet_collection_drill.py` 是 dependency-free PC gate：

- 只读取上一轮 `wave_rover_hil_packet_execution_pack` artifact 或 summary JSON。
- 不打开 serial，不读取 `/dev/*`，不 import ROS2，不调用 ROS graph，不发送 WAVE ROVER 命令。
- 输出 `schema=trashbot.wave_rover_hil_packet_collection_drill.v1`。
- 输出 `summary_schema=trashbot.wave_rover_hil_packet_collection_drill_summary.v1`。
- 输出 `evidence_boundary=software_proof_docker_wave_rover_hil_packet_collection_drill_gate`。
- 始终保持 `source=software_proof`、`overall_status=not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`same_evidence_ref_required=true`。

当上一轮 execution pack 是 `ready_for_real_hil_collection_not_proven` 时，本 gate 可以生成 `collection_drill_status=ready_for_real_hil_collection_drill_not_proven`。该状态只表示 collection drill 的 preflight checklist、材料模板、采集顺序、backfill commands 和 owner handoff 已准备好；它仍然不是 `hil_pass`。

## Input contract

支持的上一轮输入：

- `schema=trashbot.wave_rover_hil_packet_execution_pack.v1`
- 或 `summary_schema=trashbot.wave_rover_hil_packet_execution_pack_summary.v1`
- `evidence_boundary=software_proof_docker_wave_rover_hil_packet_execution_pack_gate`
- `source=software_proof`
- `overall_status=not_proven`
- `execution_pack_status=ready_for_real_hil_collection_not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control` 不得为 true
- `same_evidence_ref_required=true`
- `not_proven` 必须继续包含 `real_wave_rover`、`real_uart`、`hil_pass`、`real_odom`、`real_imu`、`real_battery`、`delivery_success`
- `required_material_templates` 必须覆盖 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 和 `operator_hil_report`

`evidence_ref` 只能是 safe token，用于跨 artifact 关联，不得携带路径、串口、波特率、checksum、traceback、credential、`/cmd_vel` 或成功断言。

## Output contract

成功生成 collection-drill artifact 时，下游只应消费以下安全字段：

- `collection_drill_status`
- safe `evidence_ref`
- `required_material_templates`
- `preflight_checklist`
- `collection_sequence`
- `backfill_commands`
- `owner_handoff`
- `blocked_reasons`
- `not_proven`
- `evidence_boundary`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

`required_material_templates` 覆盖：

- `feedback_T1001.log`
- `odom_once.jsonl`
- `imu_once.jsonl`
- `battery_once.jsonl`
- `operator_hil_report`

`preflight_checklist` 要求先锁定同一 safe `evidence_ref`，再确认 vendor 资料、真实材料采集条件和 false 控制位。它不会写入真实设备路径、baudrate、checksum、raw packet 或控制命令。

`collection_sequence` 固定为先锁定 `evidence_ref`，再采集 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`，最后写 `operator_hil_report` 并重跑 intake、review-decision 和 execution-pack gates。

`owner_handoff` 固定把真实采集交给 robot-hardware-engineer，Robot 只消费 sanitized collection-drill summary，Full-stack 保持 mobile panel 只读且 `primary_actions_enabled=false`。

## Fail-closed rules

以下情况必须 blocked：

- 缺少 execution-pack artifact/summary。
- JSON malformed 或不是 object。
- schema、summary schema、evidence boundary 或 source 不属于上一轮 execution-pack gate。
- `execution_pack_status` 不是 `ready_for_real_hil_collection_not_proven`。
- `delivery_success` 不是 false。
- `primary_actions_enabled` 不是 false。
- `safe_to_control=true`。
- `same_evidence_ref_required` 不是 true。
- `not_proven` 缺少硬件未证实 token。
- `required_material_templates` 缺少真实 HIL packet 五件套。
- `evidence_ref` 缺失、不安全或与命令行期望值不一致。
- 输入内容泄漏 `/dev/*`、`/Users/*`、`/tmp/*`、serial path、UART path、baudrate、raw path、checksum、traceback、credential 或 `/cmd_vel`。
- 输入内容出现 `delivery_success=true`、`primary_actions_enabled=true`、`safe_to_control=true` 或 `hil_pass` success claim。

失败时仍输出 `schema=trashbot.wave_rover_hil_packet_collection_drill.v1`、`overall_status=not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`，方便 Robot diagnostics 和 mobile web 只读 fail-closed。

## Example

```bash
python3 pc-tools/evidence/wave_rover_hil_packet_collection_drill.py \
  --execution-pack pc-tools/evidence/fixtures/wave_rover_hil_packet_collection_drill/execution_pack_ready.json \
  --evidence-ref hil-packet-collection-drill-fixture \
  --summary-output /tmp/wave_rover_hil_packet_collection_drill_summary.json \
  --once-json
```

## Next required evidence

真实上车前仍需补齐：

- 真实 WAVE ROVER HIL run。
- 同一个 safe `evidence_ref` 绑定整包 HIL 材料。
- 真实 `feedback_T1001.log`。
- 真实 `odom_once.jsonl`。
- 真实 `imu_once.jsonl`。
- 真实 `battery_once.jsonl`。
- 人工 `operator_hil_report`。
- PR #5 reviewer 对应线程由 reviewer 实际 resolved。

本 gate 只完成 `software_proof_docker_wave_rover_hil_packet_collection_drill_gate`，不提升为真实 HIL、真实串口、真实 2D LiDAR/ToF、PR #5 reviewer resolved 或 delivery success。
