# Verified Terminal Result Material Follow-up Escalation Status

`verified_terminal_result_material_followup_escalation_status` 是 PC-only
follow-up escalation gate。它读取上一轮
`verified_terminal_result_material_review_handoff` artifact、summary、Robot safe
alias 或兼容 wrapper，只把 terminal delivery/dropoff/cancel result 材料 handoff
转换成 field owner / support owner / reviewer 的补证跟进状态。

该 gate 不读取 raw artifacts、不访问 ROS graph、Nav2/fixed-route runtime、硬件、
真实手机、外部云、OSS/CDN、DB/queue 或 4G，也不执行任何机器人动作。
`escalated_for_terminal_result_material_followup_not_proven` 只表示人工跟进路由已形成，
不是真实送达、真实投放、真实取消完成、HIL、真实手机/browser、O5 external proof
或 reviewer-resolution。

每个输出固定保留：

- `capability=verified_terminal_result_material_followup_escalation_status`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate`
- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `no OKR percentage lift`

## Input Contract

CLI:

```bash
python3 pc-tools/evidence/verified_terminal_result_material_followup_escalation_status.py \
  --input /tmp/verified_terminal_result_material_review_handoff_summary.json \
  --output-dir /tmp/verified_terminal_result_material_followup_escalation_status
```

支持输入 schema / alias：

- `trashbot.verified_terminal_result_material_review_handoff.v1`
- `trashbot.verified_terminal_result_material_review_handoff_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_review_handoff_summary`
- `trashbot.robot_diagnostics_verified_terminal_result_material_review_handoff_summary.v1`

常见 wrapper/nested 形态也支持，例如：

- `verified_terminal_result_material_review_handoff`
- `verified_terminal_result_material_review_handoff_summary`
- `robot_diagnostics_verified_terminal_result_material_review_handoff_summary`
- `summary`
- `artifact`
- `data`
- `payload`

输入必须提供一个 safe `evidence_ref` 或 `safe_evidence_ref`，并保持所有 nested
safe summary 的 ref 一致。可选 `safe_command_id` / `command_id` 只作为短标识透传。
`terminal_result_type` 只能是：

- `delivery`
- `dropoff`
- `cancel`

## Follow-up Status Mapping

`followup_status` 只允许以下五个值：

| followup_status | Meaning |
|---|---|
| `escalated_for_terminal_result_material_followup_not_proven` | 上一轮 handoff 为 `ready_for_owner_handoff`，且 field/support/reviewer 路由安全完整；仍是 `not_proven` |
| `waiting_for_terminal_result_material_backfill_not_proven` | 上一轮 handoff 为 `needs_material_backfill`，继续等待同一 safe `evidence_ref` 的材料回填 |
| `needs_support_owner_reassignment_not_proven` | field owner、support owner 或 reviewer route 缺失，需要重新分派 |
| `rejected_unsafe_terminal_result_followup_not_proven` | 输入含 raw/unsafe fields、credentials、ROS/control details、hardware details、ACK/cursor/replay/resubmit hints、reviewer-resolution claims 或 success/control overclaims |
| `blocked_missing_terminal_result_review_handoff_not_proven` | 输入缺失、坏 JSON、unsupported schema/boundary、`evidence_ref` 不一致、unsupported `terminal_result_type` 或 source handoff 已 blocked |

## Output Files

CLI 写出：

- `verified_terminal_result_material_followup_escalation_status.json`
- `verified_terminal_result_material_followup_escalation_status_summary.json`

Artifact schema:

- `schema=trashbot.verified_terminal_result_material_followup_escalation_status.v1`
- `capability=verified_terminal_result_material_followup_escalation_status`
- `source_handoff_status=<ready_for_owner_handoff|needs_material_backfill|rejected|blocked>`
- `followup_status=<required status>`
- `safe_evidence_ref=<same safe evidence_ref or empty when blocked>`
- `safe_command_id=<safe command_id or empty>`
- `terminal_result_type=<delivery|dropoff|cancel or unsupported source value>`
- `assigned_owner=<safe short owner route>`
- `support_owner=<safe short support route>`
- `reviewer_route=<safe short reviewer route>`
- `required_material_backfill=[...]`
- `escalation_reason=<short reason>`
- `blocked_reason=<short reason or empty>`
- `next_required_evidence=[...]`
- `safe_copy=<short copy-safe string>`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `okr_lift_note=no OKR percentage lift`

Summary schema:

- `schema=trashbot.verified_terminal_result_material_followup_escalation_status_summary.v1`
- `summary_only=true`
- `safe_to_render_on_phone=true`
- `summary_alias=robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary`
- same safe fields as the artifact summary surface

Robot alias schema:

- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary.v1`
- `summary_alias=robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary`

## Refusal Rules

The gate rejects or blocks:

- raw artifacts, complete JSON dumps, raw robot responses, raw artifact paths, local paths, `file://`, `/Users/...`, `/tmp/...`, `/dev/...`
- credentials, bearer tokens, Authorization headers, signed URLs, DB/queue URLs, OSS AK/SK, passwords, cookies, access keys or API keys
- ROS/control details such as `/cmd_vel`, ROS topics, ROS graph text, command fields or control enablement fields
- hardware details such as WAVE ROVER, ESP32, Orange Pi, UART, serial device, baudrate, voltage, pins, wiring or firmware
- ACK/cursor/replay/resubmit hints, reviewer-resolution claims or GitHub thread-resolved claims
- success/control overclaims such as `delivery_success=true`, `primary_actions_enabled=true`, `safe_to_control=true`, `hil_pass=true`, `field_pass=true`, or delivery/dropoff/cancel completed wording

Blocked or rejected outputs still write sanitized artifact and summary JSON so the next
owner can see the `followup_status`, `assigned_owner`, `support_owner`,
`reviewer_route`, `required_material_backfill`, `next_required_evidence`,
`safe_copy` and fail-closed flags without receiving raw data.
