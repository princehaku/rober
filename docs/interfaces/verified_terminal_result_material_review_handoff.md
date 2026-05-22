# Verified Terminal Result Material Review Handoff

`verified_terminal_result_material_review_handoff` 是 PC-only owner handoff
gate。它读取上一轮 `verified_terminal_result_material_review_decision` artifact、
summary、Robot safe alias 或兼容 wrapper，只把 terminal delivery/dropoff/cancel
result 材料复核状态转换成 metadata-only owner handoff。

该 gate 不读取 raw artifacts、不访问 ROS graph、Nav2/fixed-route runtime、硬件、
真实手机、外部云、OSS/CDN、DB/queue 或 4G，也不执行任何机器人动作。
`ready_for_owner_handoff` 只表示脱敏 handoff package 可交给 owner，不是真实送达、
真实投放、真实取消完成、HIL、真实手机/browser 或 Objective 5 external proof。

每个输出固定保留：

- `capability=verified_terminal_result_material_review_handoff`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_review_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Input Contract

CLI:

```bash
python3 pc-tools/evidence/verified_terminal_result_material_review_handoff.py \
  --input /tmp/verified_terminal_result_material_review_decision_summary.json \
  --output-dir /tmp/verified_terminal_result_material_review_handoff
```

支持输入 schema / alias：

- `trashbot.verified_terminal_result_material_review_decision.v1`
- `trashbot.verified_terminal_result_material_review_decision_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_review_decision_summary`
- `trashbot.robot_diagnostics_verified_terminal_result_material_review_decision_summary.v1`

常见 wrapper/nested 形态也支持，例如：

- `verified_terminal_result_material_review_decision`
- `verified_terminal_result_material_review_decision_summary`
- `robot_diagnostics_verified_terminal_result_material_review_decision_summary`
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

## Handoff Mapping

`handoff_status` 只允许以下四个值：

| handoff_status | Meaning |
|---|---|
| `ready_for_owner_handoff` | 上一轮 review decision 为 `accepted_for_review`；可交给 owner，但仍是 `not_proven` |
| `needs_material_backfill` | 上一轮 review decision 要求回填材料，继续按同一 safe `evidence_ref` 补证 |
| `rejected` | 输入含 rejected/unsafe 材料、raw/unsafe fields、credentials、ROS/control details、hardware details、reviewer-resolution claims 或 success/control overclaims |
| `blocked` | 输入缺失、坏 JSON、unsupported schema/boundary、`evidence_ref` 不一致、unsupported `terminal_result_type` 或 source decision 已 blocked |

## Output Files

CLI 写出：

- `verified_terminal_result_material_review_handoff.json`
- `verified_terminal_result_material_review_handoff_summary.json`

Artifact schema:

- `schema=trashbot.verified_terminal_result_material_review_handoff.v1`
- `capability=verified_terminal_result_material_review_handoff`
- `source_review_decision=<accepted_for_review|needs_material_backfill|rejected|blocked>`
- `handoff_status=<ready_for_owner_handoff|needs_material_backfill|rejected|blocked>`
- `safe_evidence_ref=<same safe evidence_ref or empty when blocked>`
- `safe_command_id=<safe command_id or empty>`
- `terminal_result_type=<delivery|dropoff|cancel or unsupported source value>`
- `material_status_summary={accepted_material_refs,missing_required_materials,rejected_material_refs,counts,blocked_or_rejected_reasons}`
- `accepted_material_refs=[...]`
- `missing_required_materials=[...]`
- `rejected_material_refs=[...]`
- `owner_handoff={role,owner_next_action,safe_evidence_ref,safe_command_id,terminal_result_type,missing_required_materials,...}`
- `next_required_evidence=[...]`
- `blocked_reason=<short reason or empty>`
- `safe_copy=<short copy-safe string>`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Summary schema:

- `schema=trashbot.verified_terminal_result_material_review_handoff_summary.v1`
- `summary_only=true`
- `safe_to_render_on_phone=true`
- `summary_alias=robot_diagnostics_verified_terminal_result_material_review_handoff_summary`
- same safe fields as the artifact summary surface

## Refusal Rules

The gate rejects or blocks:

- raw artifacts, complete JSON dumps, raw robot responses, raw artifact paths, local paths, `file://`, `/Users/...`, `/tmp/...`, `/dev/...`
- credentials, bearer tokens, Authorization headers, signed URLs, DB/queue URLs, OSS AK/SK, passwords, cookies, access keys or API keys
- ROS/control details such as `/cmd_vel`, ROS topics, ROS graph text, command fields or control enablement fields
- hardware details such as WAVE ROVER, ESP32, Orange Pi, UART, serial device, baudrate, voltage, pins, wiring or firmware
- reviewer-resolution claims or GitHub thread-resolved claims
- success/control overclaims such as `delivery_success=true`, `primary_actions_enabled=true`, `safe_to_control=true`, `hil_pass=true`, `field_pass=true`, or delivery/dropoff/cancel completed wording

Blocked or rejected outputs still write sanitized artifact and summary JSON so the next
owner can see the `handoff_status`, `owner_handoff`, `next_required_evidence`,
`safe_copy`, material status summary and fail-closed flags without receiving raw data.
