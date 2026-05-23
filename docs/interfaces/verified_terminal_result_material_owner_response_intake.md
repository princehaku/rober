# Verified Terminal Result Material Owner Response Intake

`verified_terminal_result_material_owner_response_intake` 是 PC-only owner
response intake gate。它读取上一轮
`verified_terminal_result_material_followup_escalation_status` artifact、summary、
Robot safe alias 或兼容 wrapper，再可选读取脱敏 owner response packet，把 terminal
delivery/dropoff/cancel result 材料 owner 回复分类为 accepted、missing、rejected、
unsafe 或 blocked。

该 gate 不读取 raw artifacts、完整 JSON dump、raw owner response body、raw terminal
material，不访问 ROS graph、Nav2/fixed-route runtime、硬件、真实手机、外部云、
OSS/CDN、DB/queue、4G 或 GitHub reviewer mutation，也不执行任何机器人动作。
`accepted_terminal_result_material_owner_response_not_proven` 只表示脱敏 owner response
metadata 可进入后续 review，不是真实 delivery/dropoff/cancel result、delivery
success、HIL、真实手机/browser、O5 external proof 或 reviewer-resolution。

每个输出固定保留：

- `capability=verified_terminal_result_material_owner_response_intake`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_intake_gate`
- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `no OKR percentage lift`
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains `unresolved` / `hardware_material_pending`

## Input Contract

CLI:

```bash
python3 pc-tools/evidence/verified_terminal_result_material_owner_response_intake.py \
  --input /tmp/verified_terminal_result_material_followup_escalation_status_summary.json \
  --owner-response /tmp/sanitized_owner_response_packet.json \
  --output-dir /tmp/verified_terminal_result_material_owner_response_intake
```

`--source` 是 `--input` 的别名。`--owner-response` 可省略；省略时输出
`missing_terminal_result_material_owner_response_not_proven` 并返回非 0。

支持 source schema / alias：

- `trashbot.verified_terminal_result_material_followup_escalation_status.v1`
- `trashbot.verified_terminal_result_material_followup_escalation_status_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary`
- `trashbot.robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary.v1`

owner response packet 建议使用：

- `schema=trashbot.verified_terminal_result_material_owner_response_packet.v1`
- `source=software_proof`
- `status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `safe_evidence_ref=<same safe evidence_ref>`
- `owner_response_status=<accepted|missing|rejected|unsafe>`
- `materials` 或 `accepted_materials` / `missing_materials` / `rejected_materials` /
  `unsafe_materials`

required owner response material categories:

- `sanitized_owner_response_metadata`
- `same_safe_evidence_ref_confirmation`
- `terminal_result_material_status`
- `field_owner_acknowledgement`
- `support_owner_acknowledgement`
- `reviewer_route_confirmation`
- `pr5_hardware_material_pending_confirmation`

## Status Mapping

`owner_response_status` 只允许以下六个值：

| owner_response_status | Meaning |
|---|---|
| `accepted_terminal_result_material_owner_response_not_proven` | source follow-up status 安全，owner response 材料类别齐全且同一 safe `evidence_ref`；仍是 `not_proven` |
| `missing_terminal_result_material_owner_response_not_proven` | 缺 `--owner-response` 或缺 required owner response material category |
| `rejected_terminal_result_material_owner_response_not_proven` | owner 明确拒绝某类材料，不能进入 review |
| `unsafe_terminal_result_material_owner_response_not_proven` | owner response 含 raw/credential/path/ROS/control/hardware/ACK/replay/reviewer-resolution/success claim |
| `blocked_missing_terminal_result_followup_escalation_status_not_proven` | source 缺失、坏 JSON、unsupported schema/boundary、unsafe source 或上一轮 follow-up status 不可消费 |
| `blocked_evidence_ref_mismatch_not_proven` | source、owner response 或 CLI 指定值之间 safe `evidence_ref` 不一致 |

## Output Files

CLI 写出：

- `verified_terminal_result_material_owner_response_intake.json`
- `verified_terminal_result_material_owner_response_intake_summary.json`

Artifact schema:

- `schema=trashbot.verified_terminal_result_material_owner_response_intake.v1`
- `capability=verified_terminal_result_material_owner_response_intake`
- `source_followup_status=<上一轮 followup_status>`
- `owner_response_status=<required status>`
- `safe_evidence_ref=<same safe evidence_ref or empty when blocked>`
- `safe_command_id=<safe command_id or empty>`
- `terminal_result_type=<delivery|dropoff|cancel>`
- `field_owner=<safe short owner route>`
- `support_owner=<safe short support route>`
- `reviewer_route=<safe short reviewer route>`
- `accepted_materials=[...]`
- `missing_materials=[...]`
- `rejected_materials=[...]`
- `unsafe_materials=[...]`
- `blocked_reason=<short reason or empty>`
- `next_required_evidence=[...]`
- `safe_copy=<copy-safe object>`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `okr_lift_note=no OKR percentage lift`

Summary schema:

- `schema=trashbot.verified_terminal_result_material_owner_response_intake_summary.v1`
- `summary_only=true`
- `safe_to_render_on_phone=true`
- `summary_alias=robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary`
- same safe fields as the artifact summary surface

Robot alias schema:

- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary.v1`
- `summary_alias=robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary`

## Refusal Rules

The gate rejects or blocks:

- raw artifacts, complete JSON dumps, raw owner response body, raw terminal material, raw artifact paths, local paths, `file://`, `/Users/...`, `/tmp/...`, `/dev/...`
- credentials, bearer tokens, Authorization headers, signed URLs, DB/queue URLs, OSS AK/SK, passwords, cookies, access keys or API keys
- ROS/control details such as `/cmd_vel`, ROS topics, ROS graph text, command fields or control enablement fields
- hardware details such as WAVE ROVER, ESP32, Orange Pi, UART, serial device, baudrate, voltage, pins, wiring or firmware
- ACK/cursor/replay/resubmit hints, reviewer-resolution claims or GitHub thread-resolved claims
- success/control overclaims such as `delivery_success=true`, `primary_actions_enabled=true`, `safe_to_control=true`, `hil_pass=true`, `field_pass=true`, or delivery/dropoff/cancel completed wording

Blocked, missing, rejected or unsafe outputs still write sanitized artifact and summary JSON so
the next owner can see `source_followup_status`, `owner_response_status`, safe
`evidence_ref`, safe `command_id`, `field_owner`, `support_owner`, `reviewer_route`,
accepted/missing/rejected/unsafe material categories, `blocked_reason`,
`next_required_evidence`, `safe_copy` and fail-closed flags without receiving raw data.
