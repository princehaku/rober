# Verified Terminal Result Material Review Decision

`verified_terminal_result_material_review_decision` 是 PC-only review-decision
gate。它读取上一轮 `verified_terminal_result_material_intake` artifact、summary
或 Robot safe alias，只把 terminal delivery/dropoff/cancel result 材料状态转换成
metadata-only 复核决策。

该 gate 不读取 raw artifacts、不访问 ROS graph、Nav2/fixed-route runtime、硬件、
真实手机、外部云、OSS/CDN、DB/queue 或 4G，也不执行任何机器人动作。
`accepted_for_review` 只表示安全摘要可进入人工复核，不是真实送达、真实投放、
真实取消完成、HIL、真实手机/browser 或 Objective 5 external proof。

每个输出固定保留：

- `capability=verified_terminal_result_material_review_decision`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_review_decision_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Input Contract

CLI:

```bash
python3 pc-tools/evidence/verified_terminal_result_material_review_decision.py \
  --input /tmp/verified_terminal_result_material_intake_summary.json \
  --output-dir /tmp/verified_terminal_result_material_review_decision
```

支持输入 schema / alias：

- `trashbot.verified_terminal_result_material_intake.v1`
- `trashbot.verified_terminal_result_material_intake_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_intake_summary`
- `trashbot.robot_diagnostics_verified_terminal_result_material_intake_summary.v1`

常见 wrapper/nested 形态也支持，例如：

- `verified_terminal_result_material_intake`
- `verified_terminal_result_material_intake_summary`
- `robot_diagnostics_verified_terminal_result_material_intake_summary`
- `summary`
- `artifact`
- `data`
- `payload`

输入必须提供一个 safe `evidence_ref` 或 `safe_evidence_ref`，并保持所有 nested
safe summary 的 ref 一致。`terminal_result_type` 只能是：

- `delivery`
- `dropoff`
- `cancel`

## Decision Mapping

`review_decision` 只允许以下四个值：

| decision | Meaning |
|---|---|
| `accepted_for_review` | intake summary 没有 missing/rejected/unsafe 项，可交给人工复核；仍是 `not_proven` |
| `needs_material_backfill` | intake summary 还有缺失材料，需要同一 safe `evidence_ref` 回填 |
| `rejected` | input 含 rejected materials、raw/unsafe fields、credentials、ROS/control details、hardware details、reviewer-resolution claims 或 success/control overclaims |
| `blocked` | input 缺失、坏 JSON、unsupported schema/boundary、`evidence_ref` 不一致或 unsupported `terminal_result_type` |

## Output Files

CLI 写出：

- `verified_terminal_result_material_review_decision.json`
- `verified_terminal_result_material_review_decision_summary.json`

Artifact schema:

- `schema=trashbot.verified_terminal_result_material_review_decision.v1`
- `capability=verified_terminal_result_material_review_decision`
- `review_decision=<accepted_for_review|needs_material_backfill|rejected|blocked>`
- `safe_evidence_ref=<same safe evidence_ref or empty when blocked>`
- `terminal_result_type=<delivery|dropoff|cancel or unsupported source value>`
- `decision_reasons=[...]`
- `material_status_summary={accepted_materials,missing_materials,rejected_materials,counts,blocked_reasons}`
- `next_required_evidence=[...]`
- `owner_handoff=[...]`
- `safe_copy=<short copy-safe string>`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Summary schema:

- `schema=trashbot.verified_terminal_result_material_review_decision_summary.v1`
- `summary_only=true`
- `safe_to_render_on_phone=true`
- `summary_alias=robot_diagnostics_verified_terminal_result_material_review_decision_summary`
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
owner can see the decision, `owner_handoff`, `next_required_evidence`,
`safe_copy`, material status summary and fail-closed flags without receiving raw data.
