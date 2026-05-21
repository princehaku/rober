# Verified Terminal Result Material Intake

`verified_terminal_result_material_intake` is a dependency-free PC evidence gate
for terminal-result material intake. It reads a JSON bundle via `--input` and
writes sanitized artifact files to `--output-dir`.

The gate is intentionally fail-closed. It only prepares safe material summaries
for manual review and never proves a real delivery, dropoff, cancel, Nav2 route,
elevator field run, phone acceptance, ROS control path, HIL, or hardware state.

Every output keeps:

- `source=software_proof`
- `status=not_proven`
- `software_proof_docker_verified_terminal_result_material_intake_gate`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Input Contract

The input bundle must be a JSON object with:

- `evidence_ref`: one safe shared reference.
- `terminal_result_type`: one of `delivery`, `dropoff`, or `cancel`.
- `materials` or `material_refs`: dict or list of material objects.

Each nested material may include `evidence_ref` or `safe_evidence_ref`, but it
must match the top-level `evidence_ref`. Missing nested refs inherit the
top-level ref. Material entries may include short `summary` / `description` and
safe `material_ref` / `ref` metadata.

## Required Materials

| terminal_result_type | Required materials |
|---|---|
| `delivery` | `task_record`, `nav2_fixed_route_runtime_log`, `route_completion_signal`, `elevator_door_floor_evidence`, `human_assistance_note`, `delivery_result`, `true_phone_browser_evidence`, `diagnostics_mobile_safe_summary` |
| `dropoff` | `task_record`, `nav2_fixed_route_runtime_log`, `route_completion_signal`, `elevator_door_floor_evidence`, `human_assistance_note`, `dropoff_cancel_completion`, `true_phone_browser_evidence`, `diagnostics_mobile_safe_summary` |
| `cancel` | `task_record`, `dropoff_cancel_completion`, `true_phone_browser_evidence`, `diagnostics_mobile_safe_summary` |

`accepted_materials` only means the bundle contains safe metadata shape for
manual review. It does not prove `delivery_success`, verified terminal delivery
result, real fixed route completion, real dropoff/cancel completion, real phone
browser acceptance, or any control authority.

## Refusal Rules

The gate rejects:

- Unsupported `terminal_result_type`.
- Missing or unsafe `evidence_ref`.
- Nested material `evidence_ref` mismatch.
- Raw artifacts or raw artifact paths.
- Local paths such as `/Users/...`, `/tmp/...`, `/dev/ttyUSB*`, or `file://...`.
- Credentials, tokens, API keys, DB/queue URLs, passwords, or authorization text.
- ROS/control details such as `/cmd_vel`, ROS topics, ROS graph text, command
  fields, or control enablement fields.
- Hardware details such as WAVE ROVER, ESP32, Orange Pi, UART, serial device,
  baudrate, voltage, pins, wiring, or firmware.
- Success/control overclaims such as `delivery_success=true`,
  `primary_actions_enabled=true`, `safe_to_control=true`, `hil_pass=true`, or
  `field_pass=true`.

Blocked outputs still write sanitized artifact and summary JSON so the next
owner can see missing or rejected material names without receiving raw data.

## Output Files

The CLI writes:

- `verified_terminal_result_material_intake.json`
- `verified_terminal_result_material_intake_summary.json`

Artifact schema:

- `schema=trashbot.verified_terminal_result_material_intake.v1`
- `capability=verified_terminal_result_material_intake`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_intake_gate`
- `terminal_result_type=<delivery|dropoff|cancel or empty on rejection>`
- `same_evidence_ref_required=true`
- `accepted_materials=[...]`
- `missing_materials=[...]`
- `rejected_materials=[...]`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Summary schema:

- `schema=trashbot.verified_terminal_result_material_intake_summary.v1`
- `summary_only=true`
- `safe_to_render_on_phone=true`
- `accepted_materials=[material names only]`
- `missing_materials=[material names only]`
- `rejected_materials=[safe reasons only]`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## CLI

```bash
python3 pc-tools/evidence/verified_terminal_result_material_intake.py \
  --input /tmp/terminal_result_bundle.json \
  --output-dir /tmp/verified_terminal_result_material_intake
```

Exit code `0` means the gate generated a safe artifact. A missing-material
artifact can still exit `0` while remaining `not_proven`. Exit code `2` means the
input was unreadable, unsafe, had an unsupported terminal type, or failed the
same-`evidence_ref` requirement.
