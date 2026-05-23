# PR #5 Mandatory Sensor Material Owner-Response Intake

## Purpose

`pr5_mandatory_sensor_material_owner_response_intake` is a PC-only
software-proof gate for the unresolved PR #5 review thread
`PRRT_kwDOSWB9286CJ3tX`. It consumes the previous
`pr5_mandatory_sensor_material_followup_escalation_status` safe summary and a
sanitized owner response packet, then emits a fail-closed intake decision for
Hardware, Robot diagnostics, mobile/web, and Product review.

This interface is not a hardware driver, not a ROS control path, not a GitHub
resolution writer, and not HIL evidence.

## Vendor Source Boundary

Hardware facts for this chain start from `docs/vendor/VENDOR_INDEX.md`. The
local sources read for this gate family are:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

Those files establish source-boundary context for Orange Pi Zero 3, WAVE
ROVER, UART newline-delimited JSON, firmware command IDs, vendor app behavior,
and optional vendor-app sensor parsing. They do not prove a project 2D LiDAR
or ToF SKU/source, purchase, installation, wiring, power budget, calibration,
HIL entry, Nav2 field pass, PR #5 resolution, Objective 5 external proof, or
delivery success.

## Inputs

### `--followup-summary-json`

Required JSON object. It may be an artifact, summary, Robot alias, or wrapper
containing a safe object with:

- `schema=trashbot.pr5_mandatory_sensor_material_followup_escalation_status.v1`
  or
  `schema=trashbot.pr5_mandatory_sensor_material_followup_escalation_status_summary.v1`
- `capability=pr5_mandatory_sensor_material_followup_escalation_status`
- `evidence_boundary=software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`
- `source=software_proof`
- `hardware_material_pending`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- safe `evidence_ref`
- `same_evidence_ref_required=true`

### `--owner-response-json`

Required JSON object. It may be a direct sanitized packet or wrapper containing
`schema=trashbot.pr5_mandatory_sensor_material_owner_response_packet.v1`.
Allowed fields are owner id/role, response status, same safe `evidence_ref`,
material refs, missing refs, rejected refs, reviewer next step, and safe notes.

The packet must not contain raw artifact bodies, credentials, signed URLs, ROS
topics, `/cmd_vel`, serial/UART paths, baudrate values, WAVE ROVER parameters,
checksums, local filesystem paths, HIL/pass copy, installed-sensor claims,
delivery-success claims, or PR-resolution claims.

## Output Schemas

- Artifact: `trashbot.pr5_mandatory_sensor_material_owner_response_intake.v1`
- Summary:
  `trashbot.pr5_mandatory_sensor_material_owner_response_intake_summary.v1`
- Robot diagnostics alias:
  `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary`
- Evidence boundary:
  `software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate`

## Decisions

`decision` is one of:

- `accepted`: all required safe owner response refs are present and no unsafe
  claim is found. This is still `not_proven`.
- `missing`: required safe owner response refs are missing.
- `rejected`: owner response includes rejected refs.
- `unsafe`: packet includes raw/control/hardware/success/resolution material.
- `blocked`: source summary, schema, boundary, status, evidence ref, or
  fail-closed flags are missing or unsupported.

Every decision preserves `source=software_proof`, `hardware_material_pending`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

## Required Safe Owner Response Refs

- 2D LiDAR SKU/source/receipt/procurement material owner response
- ToF SKU/source/receipt/procurement material owner response
- mounting/installation material owner response
- wiring and power-budget material owner response
- calibration plan or calibration result owner response
- HIL-entry material owner response
- operator HIL report owner response
- PR #5 reviewer follow-up or reviewer resolution owner response

These refs are tracking labels only. They are not raw artifacts and not proof
that the real materials exist.

## Safe Summary Contract

The summary exposes only:

- `decision`
- `allowed_decisions`
- `decision_reasons`
- safe `evidence_ref`
- `followup_escalation_status`
- `safe_owner_response_packet`
- `required_owner_response_refs`
- `material_status`
- `safe_lineage`
- `owner_handoff`
- `next_required_evidence`
- `rerun_commands`
- `safe_copy`
- `non_access_scope`
- false control/success flags

It does not expose raw owner artifact bodies or low-level runtime details.

## Non-Access Scope

The gate does not read ROS graph, GitHub write or review-thread resolution
state, serial/UART devices, WAVE ROVER runtime, real 2D LiDAR, real ToF,
sensor drivers, HIL rigs, field runs, Objective 5 external infrastructure,
network resources, delivery execution state, raw vendor files, or raw artifact
bodies.

## CLI

```bash
python3 pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_intake.py \
  --followup-summary-json /tmp/pr5_mandatory_sensor_material_followup_escalation_status_summary.json \
  --owner-response-json /tmp/pr5_mandatory_sensor_material_owner_response_packet.json \
  --evidence-ref pr5-material-owner-response-001 \
  --output /tmp/pr5_mandatory_sensor_material_owner_response_intake.json \
  --summary-output /tmp/pr5_mandatory_sensor_material_owner_response_intake_summary.json
```

The CLI returns `0` only for `accepted`. It returns non-zero for `missing`,
`rejected`, `unsafe`, or `blocked`.
