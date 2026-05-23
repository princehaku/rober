# Verified Terminal Result Material Owner Response Review Handoff

`verified_terminal_result_material_owner_response_review_handoff` 是 PC-only owner
response review handoff gate。它读取上一轮
`verified_terminal_result_material_owner_response_review_decision` artifact、summary、
Robot safe alias 或兼容 wrapper，把 safe metadata 派生成 owner/support/reviewer
handoff packet。

该 gate 不读取 raw artifacts、完整 JSON dump、raw owner response body、raw terminal
material，不访问 ROS graph、Nav2/fixed-route runtime、硬件、真实手机、外部云、
public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover
或 GitHub reviewer mutation，也不执行任何机器人动作。
`accepted_terminal_result_material_owner_response_review_handoff_not_proven` 只表示
脱敏 handoff packet 可以交给 field owner、support owner 和 reviewer 继续人工补证，
不是真实 delivery/dropoff/cancel result、delivery success、route/elevator field pass、
HIL、真实手机/browser、WAVE ROVER/UART proof、O5 external proof 或 reviewer-resolution。

每个输出固定保留：

- `capability=verified_terminal_result_material_owner_response_review_handoff`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate`
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
python3 pc-tools/evidence/verified_terminal_result_material_owner_response_review_handoff.py \
  --input /tmp/verified_terminal_result_material_owner_response_review_decision_summary.json \
  --output-dir /tmp/verified_terminal_result_material_owner_response_review_handoff
```

`--source` 是 `--input` 的别名。`--evidence-ref` 可选；提供时必须与 source 中
safe `evidence_ref` 完全一致。

支持 source schema / alias：

- `trashbot.verified_terminal_result_material_owner_response_review_decision.v1`
- `trashbot.verified_terminal_result_material_owner_response_review_decision_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary`
- `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary.v1`

source 必须保留：

- `source=software_proof`
- `status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate`
- `safe_evidence_ref=<same safe evidence_ref>`
- `review_decision=<上一轮 owner response review decision status>`
- `terminal_result_type=<delivery|dropoff|cancel>`
- owner/support/reviewer route
- accepted/missing/rejected/unsafe material category lists

## Status Mapping

`handoff_status` 只允许以下六个值：

| handoff_status | Meaning |
|---|---|
| `accepted_terminal_result_material_owner_response_review_handoff_not_proven` | source decision 安全且 accepted；仍是 `not_proven` |
| `missing_terminal_result_material_owner_response_review_handoff_not_proven` | source decision 表示材料缺失或无法进入最终交接 |
| `rejected_terminal_result_material_owner_response_review_handoff_not_proven` | source decision 表示 owner response review material 被拒绝 |
| `unsafe_terminal_result_material_owner_response_review_handoff_not_proven` | source 或嵌套文本含 raw/credential/path/ROS/control/hardware/ACK/replay/reviewer-resolution/success claim |
| `blocked_missing_terminal_result_owner_response_review_decision_not_proven` | source 缺失、坏 JSON、unsupported schema 或缺上一轮 decision boundary |
| `blocked_evidence_ref_mismatch_not_proven` | source 与 CLI 指定值之间 safe `evidence_ref` 不一致 |

## Output Files

CLI 写出：

- `verified_terminal_result_material_owner_response_review_handoff.json`
- `verified_terminal_result_material_owner_response_review_handoff_summary.json`

Artifact schema:

- `schema=trashbot.verified_terminal_result_material_owner_response_review_handoff.v1`
- `capability=verified_terminal_result_material_owner_response_review_handoff`
- `source_schema=<上一轮 review decision schema>`
- `source_review_decision=<上一轮 review_decision>`
- `handoff_status=<required status>`
- `safe_evidence_ref=<same safe evidence_ref or missing_safe_evidence_ref when blocked>`
- `safe_command_id=<safe command_id or empty>`
- `terminal_result_type=<delivery|dropoff|cancel>`
- `field_owner=<safe short owner route>`
- `support_owner=<safe short support route>`
- `reviewer_route=<safe short reviewer route>`
- `owner_handoff=<copy-safe object>`
- `support_handoff=<copy-safe object>`
- `reviewer_handoff=<copy-safe object>`
- `accepted_materials=[...]`
- `missing_materials=[...]`
- `rejected_materials=[...]`
- `unsafe_materials=[...]`
- `blocked_reason=<short reason or empty>`
- `handoff_reasons=[...]`
- `next_required_evidence=[...]`
- `safe_copy=<copy-safe object>`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `okr_lift_note=no OKR percentage lift`

Summary schema:

- `schema=trashbot.verified_terminal_result_material_owner_response_review_handoff_summary.v1`
- `summary_only=true`
- `safe_to_render_on_phone=true`
- `summary_alias=robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary`
- same safe fields as the artifact summary surface

Robot alias schema:

- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary.v1`
- `summary_alias=robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary`

## Refusal Rules

The gate rejects or blocks:

- raw artifacts, complete JSON dumps, raw owner response body, raw terminal material, raw artifact paths, local paths, `file://`, `/Users/...`, `/tmp/...`, `/dev/...`
- credentials, bearer tokens, Authorization headers, signed URLs, DB/queue URLs, OSS AK/SK, passwords, cookies, access keys or API keys
- public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover or external O5 proof claims
- ROS/control details such as `/cmd_vel`, ROS topics, ROS graph text, command fields or control enablement fields
- hardware details such as WAVE ROVER, ESP32, Orange Pi, UART, serial device, baudrate, voltage, pins, wiring or firmware
- ACK/cursor/replay/resubmit hints, reviewer-resolution claims or GitHub thread-resolved claims
- success/control overclaims such as `delivery_success=true`, `primary_actions_enabled=true`, `safe_to_control=true`, `hil_pass=true`, `field_pass=true`, or delivery/dropoff/cancel completed wording

Blocked, missing, rejected or unsafe outputs still write sanitized artifact and summary JSON so
the next owner can see source decision, safe `evidence_ref`, safe `command_id`,
`field_owner`, `support_owner`, `reviewer_route`, handoff routes, material categories,
`blocked_reason`, `next_required_evidence`, `safe_copy` and fail-closed flags without
receiving raw data.
