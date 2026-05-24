# PR #5 Mandatory Sensor Material Owner Response Reviewer ACK Intake

`pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake` is a
PC-only evidence gate. It consumes the previous
`pr5_mandatory_sensor_material_owner_response_review_handoff` safe artifact,
summary, Robot alias, or wrapper and may also consume an optional sanitized
reviewer ACK packet. It emits reviewer ACK intake metadata for Robot/mobile/
Product consumption.

This gate is not a hardware driver, not a ROS control path, not a GitHub
resolution writer, not a WAVE ROVER/UART/HIL check, and not proof that LiDAR or
ToF material is installed.

## Vendor Source Boundary

The source attribution chain starts at `docs/vendor/VENDOR_INDEX.md`. The local
vendor refs read for this gate family are:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf`
- `docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

Those files support source attribution for Orange Pi Zero 3, WAVE ROVER,
newline-delimited UART JSON, firmware command IDs, vendor app behavior, and
hardware-source discipline. They do not prove real project sensor material,
WAVE ROVER runtime, serial/UART communication, wiring, power, calibration,
operator HIL, PR #5 resolution, Objective 5 external proof, or delivery
success.

## Input

`--owner-response-review-handoff-json` is required. It may point to a
sanitized artifact, summary, Robot alias, or wrapper containing:

- `schema=trashbot.pr5_mandatory_sensor_material_owner_response_review_handoff.v1`
  or
  `schema=trashbot.pr5_mandatory_sensor_material_owner_response_review_handoff_summary.v1`
- `capability=pr5_mandatory_sensor_material_owner_response_review_handoff`
- `evidence_boundary=software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`
- `handoff_status=ready_for_owner_response_review_handoff_not_proven`
- `source=software_proof`
- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- safe `evidence_ref`

`--reviewer-ack-json` is optional. When provided, it must be sanitized reviewer
metadata under `schema=trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_packet.v1`
or a minimal safe ACK form. Accepted ACK fields are limited to reviewer role,
reviewer identity label, ACK reason, owner/support/reviewer next steps,
optional reassignment target, `next_required_evidence`, and the same safe
`evidence_ref`.

## Output Schemas

- Artifact:
  `trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.v1`
- Summary:
  `trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary.v1`
- Robot diagnostics alias:
  `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary`
- Evidence boundary:
  `software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate`

## Reviewer ACK States

`reviewer_ack_state` is one of:

- `accepted_acknowledged_not_proven`
- `needs_reassignment`
- `blocked_missing_handoff`
- `rejected_unsafe_ack`
- `evidence_ref_mismatch`

Every state preserves `source=software_proof`, `hardware_material_pending`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

`accepted_acknowledged_not_proven` means only that the reviewer-safe ACK packet
matches the previous safe handoff under the same safe `evidence_ref`. It does
not resolve `PRRT_kwDOSWB9286CJ3tX`, does not prove real 2D LiDAR or ToF
material, and does not prove HIL or delivery success.

## Fail-Closed Rules

The gate emits a non-accepted state when any of these are true:

- Missing, unreadable, bad, unsupported, or non-ready handoff source.
- Missing safe `evidence_ref` or source/ACK/requested `evidence_ref` mismatch.
- Handoff or ACK does not preserve `software_proof`,
  `hardware_material_pending`, `not_proven`, `delivery_success=false`,
  `primary_actions_enabled=false`, or `safe_to_control=false`.
- Reviewer ACK is missing or incomplete; this maps to `needs_reassignment`
  because the ACK packet is optional but not sufficient for acknowledged state.
- Raw artifact/body/material, local path, credential, signed URL, DB/queue URL,
  ROS topic, `/cmd_vel`, serial/UART, baudrate, WAVE ROVER runtime proof,
  GitHub resolution/mutation, HIL/pass, installed LiDAR/ToF, delivery success,
  or control-enabled claim appears in source wrappers or ACK input.

## Safe Summary Contract

The summary exposes only:

- `reviewer_ack_state`
- `allowed_reviewer_ack_states`
- `ack_reasons`
- safe `evidence_ref`
- `source_owner_response_review_handoff`
- `reviewer_acknowledgement`
- `next_required_evidence`
- `rerun_commands`
- `vendor_source_refs`
- `vendor_source_boundary=source_attribution_only_not_real_sensor_or_hil_proof`
- `safe_copy`
- `non_access_scope`
- false success/control flags

It does not expose raw owner-response handoff bodies, raw reviewer ACK bodies,
real material payloads, serial/UART paths, ROS topics, WAVE ROVER runtime
parameters, or GitHub mutation state.

## CLI

```bash
python3 pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py \
  --owner-response-review-handoff-json /tmp/pr5_mandatory_sensor_material_owner_response_review_handoff_summary.json \
  --reviewer-ack-json /tmp/pr5_mandatory_sensor_material_owner_response_reviewer_ack_packet.json \
  --evidence-ref pr5-reviewer-ack-001 \
  --output /tmp/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.json \
  --summary-output /tmp/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary.json
```

The CLI returns `0` for `accepted_acknowledged_not_proven` and
`needs_reassignment` only when a supported safe reassignment ACK packet is
provided. It returns non-zero for missing ACK metadata, missing/unsupported
handoff, unsafe input, and evidence-ref mismatch.
