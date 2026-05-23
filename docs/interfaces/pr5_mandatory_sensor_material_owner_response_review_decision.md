# PR #5 Mandatory Sensor Material Owner-Response Review Decision

## Purpose

`pr5_mandatory_sensor_material_owner_response_review_decision` is a PC-only
software-proof gate for unresolved PR #5 review thread `PRRT_kwDOSWB9286CJ3tX`.
It consumes only the sanitized
`pr5_mandatory_sensor_material_owner_response_intake` artifact/summary fields
and emits a fail-closed reviewer closeout decision for Hardware, Robot
diagnostics, mobile/web, and Product review.

This interface is not a hardware driver, not a ROS control path, not a GitHub
resolution writer, not a sensor-material reader, and not HIL evidence.

## Vendor Source Boundary

Hardware facts for this chain start from `docs/vendor/VENDOR_INDEX.md`. The
local refs read for this gate family are:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf`
- `docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

Those files establish source-boundary context for Orange Pi Zero 3, WAVE
ROVER, UART newline-delimited JSON, firmware command IDs, vendor app behavior,
and source attribution discipline. They do not prove a real project 2D LiDAR
or ToF SKU/source, receipt, procurement, installation, wiring, power budget,
calibration, HIL entry, operator HIL report, PR #5 resolution, Objective 5
external proof, or delivery success.

## Input

### `--owner-response-intake-json`

Required JSON object. It may be an artifact, summary, Robot alias, or wrapper
containing a safe object with:

- `schema=trashbot.pr5_mandatory_sensor_material_owner_response_intake.v1`
  or
  `schema=trashbot.pr5_mandatory_sensor_material_owner_response_intake_summary.v1`
- `capability=pr5_mandatory_sensor_material_owner_response_intake`
- `evidence_boundary=software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate`
- `source=software_proof`
- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- safe `evidence_ref`
- `same_evidence_ref_required=true`
- sanitized intake `decision` and `material_status`

The gate must not consume raw owner-response body text, complete artifacts,
real material payloads, credentials, signed URLs, local filesystem paths,
checksums, ROS topics, `/cmd_vel`, serial/UART paths, baudrate values, HIL/pass
copy, PR-resolution claims, Objective 5 external proof claims, or delivery
success claims.

## Output Schemas

- Artifact:
  `trashbot.pr5_mandatory_sensor_material_owner_response_review_decision.v1`
- Summary:
  `trashbot.pr5_mandatory_sensor_material_owner_response_review_decision_summary.v1`
- Robot diagnostics alias:
  `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary`
- Evidence boundary:
  `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate`

## Review Decisions

`review_decision` is one of:

- `accepted_for_reviewer_closeout_not_proven`
- `needs_more_material_not_proven`
- `rejected_unsafe_material_not_proven`
- `blocked_missing_owner_response_intake_not_proven`
- `blocked_evidence_ref_mismatch_not_proven`

Every decision preserves `source=software_proof`, `hardware_material_pending`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

`accepted_for_reviewer_closeout_not_proven` means only that the sanitized intake
metadata can be considered by a human reviewer for closeout. It does not prove
real sensor material and does not resolve `PRRT_kwDOSWB9286CJ3tX`.

## Fail-Closed Rules

The gate emits a non-accepted state when any of these are true:

- Missing JSON, unreadable JSON, bad JSON, or non-object JSON.
- Unsupported source schema, capability, or evidence boundary.
- Missing safe `evidence_ref`.
- Source and requested `evidence_ref` mismatch.
- Source does not preserve `software_proof`, `hardware_material_pending`,
  `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, or
  `safe_to_control=false`.
- Source intake decision is not accepted, missing, rejected, or unsafe.
- Raw owner-response body, raw artifact, complete JSON, credential, signed URL,
  local path, checksum, traceback, ROS topic, `/cmd_vel`, serial/UART path,
  baudrate, HIL/pass copy, installed-sensor proof claim, PR resolved claim,
  Objective 5 external proof claim, delivery success claim, or control-enabled
  claim appears in the source.

## Safe Summary Contract

The summary exposes only:

- `review_decision`
- `allowed_review_decisions`
- `decision_reasons`
- safe `evidence_ref`
- `source_owner_response_intake`
- `material_status`
- `owner_handoff`
- `next_required_evidence`
- `rerun_commands`
- `vendor_source_refs`
- `vendor_source_boundary=source_attribution_only_not_real_sensor_proof`
- `safe_copy`
- `non_access_scope`
- false control/success flags

It does not expose raw owner response bodies, real material payloads, low-level
WAVE ROVER parameters, serial/UART paths, ROS topics, or GitHub mutation state.

## Non-Access Scope

The gate does not read ROS graph, GitHub write or review-thread resolution
state, serial/UART devices, WAVE ROVER runtime, Orange Pi runtime, real 2D
LiDAR, real ToF, sensor drivers, HIL rigs, field runs, Objective 5 external
infrastructure, network resources, delivery execution state, raw vendor files,
or raw owner response bodies.

## CLI

```bash
python3 pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_review_decision.py \
  --owner-response-intake-json /tmp/pr5_mandatory_sensor_material_owner_response_intake_summary.json \
  --evidence-ref pr5-material-owner-response-001 \
  --output /tmp/pr5_mandatory_sensor_material_owner_response_review_decision.json \
  --summary-output /tmp/pr5_mandatory_sensor_material_owner_response_review_decision_summary.json
```

The CLI returns `0` only for
`accepted_for_reviewer_closeout_not_proven`. It returns non-zero for
`needs_more_material_not_proven`, `rejected_unsafe_material_not_proven`,
`blocked_missing_owner_response_intake_not_proven`, or
`blocked_evidence_ref_mismatch_not_proven`.
