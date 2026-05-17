# WAVE ROVER HIL Packet Execution Pack Gate

## Vendor sources

本 gate 的硬件事实只采用本地 vendor 资料：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

已证实的 vendor 结论：

- WAVE ROVER 上下位机链路是 UART newline-delimited JSON。
- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO 1001`，真实 packet 的 `feedback_T1001.log` 必须来自 `T=1001` base feedback。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK 130`、`CMD_BASE_FEEDBACK_FLOW 131`、`CMD_FEEDBACK_FLOW_INTERVAL 142` 和 `CMD_UART_ECHO_MODE 143`。
- `uart_ctrl.h` 按 JSON 字段 `T` 分发命令，包含 base feedback、feedback flow、feedback interval 和 UART echo mode 分支。
- `base_ctrl.py` 使用 `json.loads(...readline...)` 读取一行 JSON，并使用 `json.dumps(data) + '\n'` 发送命令。
- `config.yaml` 是 vendor upper-computer 的 command ID、feedback key、速度和 `feedback_interval` 配置参考。

这些来源只证明协议和配置出处，不证明本轮存在真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery` 或 `hil_pass`。

## Scope

`pc-tools/evidence/wave_rover_hil_packet_execution_pack.py` 是 dependency-free PC gate：

- 只读取上一轮 `wave_rover_hil_packet_review_decision` artifact 或 summary JSON。
- 不打开 serial，不读取 `/dev/*`，不 import ROS2，不调用 ROS graph。
- 输出 `schema=trashbot.wave_rover_hil_packet_execution_pack.v1`。
- 输出 `summary_schema=trashbot.wave_rover_hil_packet_execution_pack_summary.v1`。
- 输出 `evidence_boundary=software_proof_docker_wave_rover_hil_packet_execution_pack_gate`。
- 始终保持 `source=software_proof`、`overall_status=not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`same_evidence_ref_required=true`。

当上一轮 review decision 是 `blocked_pending_real_hil_packet` 时，本 gate 可以生成 `execution_pack_status=ready_for_real_hil_collection_not_proven`。该状态只表示材料模板、采集顺序、owner handoff、backfill guidance 和 rerun commands 已准备好；它仍然不是 `hil_pass`。

## Input contract

支持的上一轮输入：

- `schema=trashbot.wave_rover_hil_packet_review_decision.v1`
- 或 `summary_schema=trashbot.wave_rover_hil_packet_review_decision_summary.v1`
- `evidence_boundary=software_proof_docker_wave_rover_hil_packet_review_decision_gate`
- `source=software_proof`
- `overall_status=not_proven`
- `review_decision=blocked_pending_real_hil_packet`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`
- `not_proven` 必须包含 `real_wave_rover`、`real_uart`、`hil_pass`、`real_odom`、`real_imu`、`real_battery`、`delivery_success`
- `next_required_evidence` 必须覆盖真实 WAVE ROVER HIL run、same evidence_ref HIL packet、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 和 `operator_hil_report`
- `missing_required_materials` 必须继续声明真实 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 和 `operator_hil_report`

`evidence_ref` 只能是 safe token，用于跨 artifact 关联，不得携带路径、串口、波特率、checksum、traceback 或凭证。

## Output contract

成功生成 execution-pack artifact 时，下游只应消费以下安全字段：

- `execution_pack_status`
- `required_material_templates`
- `collection_sequence`
- `owner_handoff`
- `backfill_guidance`
- `rerun_commands`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

`required_material_templates` 覆盖：

- `feedback_T1001.log`
- `odom_once.jsonl`
- `imu_once.jsonl`
- `battery_once.jsonl`
- `operator_hil_report`

`collection_sequence` 固定为先确认真实硬件环境，再按同一 `evidence_ref` 采集 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`，最后写 `operator_hil_report` 并重跑 intake 与 review decision gates。

`owner_handoff` 固定把真实采集交给 hardware-engineer，Robot 只读消费 review-decision summary，Full-stack 保持 mobile execution pack 只读且 `primary_actions_enabled=false`。

## Fail-closed rules

以下情况必须 blocked：

- 缺少 review-decision artifact/summary。
- JSON malformed 或不是 object。
- schema、summary schema、evidence boundary 或 source 不属于上一轮 review-decision gate。
- `review_decision` 不是 `blocked_pending_real_hil_packet`。
- `delivery_success` 不是 false。
- `primary_actions_enabled` 不是 false。
- `same_evidence_ref_required` 不是 true。
- `not_proven` 缺少硬件未证实 token。
- `next_required_evidence` 或 `missing_required_materials` 缺少真实 HIL packet 材料。
- `evidence_ref` 缺失、不安全或与命令行期望值不一致。
- 输入内容泄漏 `/dev/*`、`/Users/*`、`/tmp/*`、serial、baudrate、raw path、checksum、traceback、credential。
- 输入内容出现 `delivery_success=true`、`primary_actions_enabled=true` 或 `hil_pass` success claim。

失败时仍输出 `schema=trashbot.wave_rover_hil_packet_execution_pack.v1`、`overall_status=not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，方便 Robot diagnostics 和 mobile web 只读 fail-closed。

## Example

```bash
python3 pc-tools/evidence/wave_rover_hil_packet_execution_pack.py \
  --review-summary pc-tools/evidence/fixtures/wave_rover_hil_packet_execution_pack/review_ready.json \
  --evidence-ref hil-packet-execution-fixture \
  --summary-output /tmp/wave_rover_hil_packet_execution_pack_summary.json \
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

本 gate 只完成 `software_proof_docker_wave_rover_hil_packet_execution_pack_gate`，不提升为真实 HIL、真实串口或 delivery success。
