# Verified Terminal Result Material Owner Response Reviewer ACK Intake

`verified_terminal_result_material_owner_response_reviewer_ack_intake` 是 PC-only
reviewer ACK intake gate。它读取上一轮
`verified_terminal_result_material_owner_response_review_handoff` artifact、summary、
Robot safe alias 或兼容 wrapper，再读取一个脱敏 reviewer ACK packet，把同一 safe
`evidence_ref` 下的 ACK 转成 reviewer ACK intake artifact/summary。

该 gate 不读取 raw artifacts、raw terminal result material、raw reviewer ACK body、
完整 JSON dump、ROS graph、Nav2/fixed-route runtime、硬件、真实手机、外部云、
public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 GitHub reviewer
mutation，也不执行任何机器人动作。`reviewer_acknowledged_not_proven` 只表示 reviewer
已收到上一跳 safe metadata；不是真实 delivery/dropoff/cancel result、delivery success、
route/elevator field pass、HIL、真实 phone/browser proof、WAVE ROVER/UART proof、O5
external proof 或 PR #5 reviewer resolution。

每个输出固定保留：

- `capability=verified_terminal_result_material_owner_response_reviewer_ack_intake`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate`
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
python3 pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_intake.py \
  --owner-response-review-handoff-json /tmp/verified_terminal_result_material_owner_response_review_handoff_summary.json \
  --reviewer-ack-json /tmp/verified_terminal_result_material_owner_response_reviewer_ack_packet.json \
  --output-dir /tmp/verified_terminal_result_material_owner_response_reviewer_ack_intake
```

`--evidence-ref` 可选；提供时必须与上一跳 handoff 和 reviewer ACK packet 中的 safe
`evidence_ref` 完全一致。

支持上一跳 source schema / alias：

- `trashbot.verified_terminal_result_material_owner_response_review_handoff.v1`
- `trashbot.verified_terminal_result_material_owner_response_review_handoff_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary`
- `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary.v1`

source 必须保留：

- `source=software_proof`
- `status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate`
- `safe_evidence_ref=<same safe evidence_ref>`
- `handoff_status=accepted_terminal_result_material_owner_response_review_handoff_not_proven`
- safe `command_id` when available
- `terminal_result_type=<delivery|dropoff|cancel>` when available

reviewer ACK packet schema:

- `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_packet.v1`

ACK packet safe fields:

- `source=software_proof`
- `status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `safe_evidence_ref=<same safe evidence_ref>`
- `reviewer_ack_state=<acknowledged|needs_reassignment canonical value>`
- `reviewer_role`
- `reviewer_identity_label`
- `ack_reason`
- `owner_next_step`
- `support_next_step`
- `reviewer_next_step`
- `next_required_evidence`
- optional `reassignment_target` when `reviewer_ack_state=reviewer_ack_needs_reassignment`

## Status Mapping

`reviewer_ack_state` 只允许以下五个值：

| reviewer_ack_state | Meaning |
|---|---|
| `reviewer_acknowledged_not_proven` | reviewer ACK complete under same safe `evidence_ref`; still `not_proven` |
| `reviewer_ack_needs_reassignment` | reviewer ACK requires safe reassignment or lacks required reviewer fields |
| `reviewer_ack_evidence_ref_mismatch` | source, ACK, or CLI safe `evidence_ref` does not match |
| `reviewer_ack_rejected_unsafe` | source or ACK contains raw/path/credential/ROS/control/hardware/HIL/O5/PR #5 resolution/success claim |
| `blocked_missing_terminal_result_owner_response_review_handoff` | source handoff or ACK JSON is missing, bad, unsupported, or not accepted |

## Output Files

CLI 写出：

- `verified_terminal_result_material_owner_response_reviewer_ack_intake.json`
- `verified_terminal_result_material_owner_response_reviewer_ack_intake_summary.json`

Artifact schema:

- `schema=trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake.v1`
- `capability=verified_terminal_result_material_owner_response_reviewer_ack_intake`
- `source_capability=verified_terminal_result_material_owner_response_review_handoff`
- `source_schema=<上一轮 handoff schema>`
- `source_evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate`
- `reviewer_ack_state=<required status>`
- `safe_evidence_ref=<same safe evidence_ref or missing_safe_evidence_ref when blocked>`
- `safe_command_id=<safe command_id or empty>`
- `terminal_result_type=<delivery|dropoff|cancel or empty>`
- `source_owner_response_review_handoff=<copy-safe object>`
- `reviewer_acknowledgement=<copy-safe object>`
- `ack_reasons=[...]`
- `next_required_evidence=[...]`
- `safe_copy=<copy-safe object>`
- `pr5_thread.state=unresolved`
- `pr5_thread.material_state=hardware_material_pending`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `okr_lift_note=no OKR percentage lift`

Summary schema:

- `schema=trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake_summary.v1`
- `summary_only=true`
- `safe_to_render_on_phone=true`
- `summary_alias=robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary`
- same safe fields as the artifact summary surface

Robot alias name:

- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary`

## Refusal Rules

The gate rejects or blocks:

- raw artifacts, complete JSON dumps, raw reviewer ACK body, raw terminal material, raw artifact paths, local paths, `file://`, `/Users/...`, `/tmp/...`, `/dev/...`
- credentials, bearer tokens, Authorization headers, signed URLs, DB/queue URLs, OSS AK/SK, passwords, cookies, access keys or API keys
- public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue or external O5 proof claims
- ROS/control details such as `/cmd_vel`, ROS topics, ROS graph text, command fields or control enablement fields
- hardware details such as WAVE ROVER, ESP32, Orange Pi, UART, serial device, baudrate, voltage, pins, wiring or firmware
- HIL pass, route/elevator field pass, true phone/browser proof, real terminal result, PR #5 resolved wording or GitHub thread-resolved claims
- success/control overclaims such as `delivery_success=true`, `primary_actions_enabled=true`, `safe_to_control=true`, or delivery/dropoff/cancel completed wording

Blocked, reassignment, mismatch or unsafe outputs still write sanitized artifact and summary JSON so
Robot diagnostics and mobile/web can render the fail-closed state without receiving raw data or enabling
primary actions.
