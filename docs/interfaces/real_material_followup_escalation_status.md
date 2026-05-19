# Real Material Followup Escalation Status

`real_material_followup_escalation_status` is a dependency-free PC evidence gate
for the follow-up state after `real_material_readiness_board`,
`real_material_evidence_intake`, and `real_material_manifest_template`.

It is an escalation status surface, not a proof surface. Every artifact and
summary remains:

- `source=software_proof`
- `status=not_proven`
- `evidence_boundary=software_proof_docker_real_material_followup_escalation_status_gate`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Vendor Source Boundary

Hardware-related fields cite `docs/vendor/VENDOR_INDEX.md` as the required local
entry point. The gate references:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

These sources establish only the local WAVE ROVER / UART JSON / firmware source
boundary. They do not prove real external cloud material, real WAVE ROVER UART
feedback, HIL packet success, 2D LiDAR SKU/source/receipt, ToF
SKU/source/receipt, installation, wiring, power, calibration, real phone/browser
acceptance, route/elevator field pass, or delivery success.

## Schemas

Artifact schema:

- `schema=trashbot.real_material_followup_escalation_status.v1`
- `real_material_followup_escalation_status=blocked_pending_real_materials`
- `safe_evidence_ref=<shared safe evidence_ref>`
- `source_template_status=ready_for_field_owner_submission_pack_not_proven`
- `source_intake_status=blocked_missing_real_material_items`
- `material_groups=[...]`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Summary schema:

- `schema=trashbot.real_material_followup_escalation_status_summary.v1`
- `summary_only=true`
- `safe_to_render_on_phone=true`
- `group_count=4`
- `blocked_group_count=4`
- `escalation_required_count=4`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Material Groups

Each group includes:

- `material_group`
- `safe_evidence_ref`
- `field_owner`
- `due_status`
- `blocked_reason`
- `next_required_evidence`
- `escalation_level`
- `rerun_command`
- `rerun_status_summary`
- `source_template_status`
- `source_intake_status`
- `review_route`
- `evidence_boundary`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

| material_group | Objective / review ref | Owner handoff | Follow-up boundary |
|---|---|---|---|
| `o5_external` | `Objective 5` | `product-okr-owner` | Missing real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker migration/cutover, and external proof. |
| `o1_pr5_hardware` | `Objective 1`, `PR #5`, `PRRT_kwDOSWB9286CJ3tX` | `hardware-engineer` | `blocked_pending_real_materials`; missing mandatory sensor baseline citation to `docs/vendor/VENDOR_INDEX.md` and real 2D LiDAR / ToF / WAVE ROVER UART/HIL material. |
| `pr4_route_elevator` | `PR #4`, `Objective 2`, `Objective 3` | `autonomy-engineer` | Missing real Nav2/fixed-route runtime log, route completion signal, field task record, elevator door state, target floor confirmation, human assistance record, dropoff/cancel material, and `delivery_result`. |
| `o4_real_phone` | `Objective 4` | `full-stack-software-engineer` | Missing real phone browser/device/PWA/user-choice acceptance material. |

## O1 / PR #5 Mandatory Sensor Baseline

The O1 / PR #5 group must preserve:

- `review_thread_id=PRRT_kwDOSWB9286CJ3tX`
- `review_thread_state=blocked_pending_real_materials`
- `mandatory_sensor_baseline_citation=docs/vendor/VENDOR_INDEX.md plus referenced docs/vendor sources required before review can move`
- `next_required_evidence` for real 2D LiDAR / ToF SKU/source/receipt,
  mounting, wiring, power, calibration, HIL-entry, WAVE ROVER UART/HIL packet,
  `feedback_T1001`, odom, imu, battery, and operator signoff.

This status still does not close PR #5 and does not prove hardware readiness.

## CLI

```bash
python3 pc-tools/evidence/real_material_followup_escalation_status.py \
  --output sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status.json \
  --summary-output sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status_summary.json
```

The exit code is `0` when the gate generated a fail-closed status artifact.
It returns non-zero when `docs/vendor/VENDOR_INDEX.md` is missing, the
`evidence_ref` is unsafe, or output contains a forbidden success/control,
credential, absolute path, or raw serial/UART path signal.

## Fail-Closed Rules

The gate must remain blocked when:

- Objective 5 still lacks real external cloud/network/data-plane proof.
- Objective 1 / PR #5 still lacks `docs/vendor/` source citation plus real 2D
  LiDAR / ToF / WAVE ROVER/HIL material.
- PR #4 still lacks real route/elevator field material.
- Objective 4 still lacks real phone/browser material.
- Any output tries to claim `delivery_success=true`,
  `primary_actions_enabled=true`, `safe_to_control=true`, `hil_pass=true`, or
  `field_pass=true`.

`real_material_followup_escalation_status` therefore stays
`software_proof_docker_real_material_followup_escalation_status_gate`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.
