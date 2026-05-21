# Field Evidence Real Material Response Review Handoff Tech Plan

Run time: 2026-05-21 17:18 CST

## Capability

- capability: `field_evidence_real_material_response_review_handoff`
- evidence boundary: `software_proof_docker_field_evidence_real_material_response_review_handoff_gate`
- sprint_type: epic
- planning owner: Product Manager / OKR Owner
- execution owners: Autonomy, Robot Platform, Full-Stack, Hardware consultation, Product closeout

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1 is Objective 5 at about 68%.
2. This sprint does not target Objective 5 percentage movement because real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/migration/cutover, production app/device, and true phone/browser evidence are still missing. Per the stop rule in `OKR.md` section 6, adding another local O5 metadata wrapper is not meaningful progress.
3. The next lowest Objective is Objective 1 at about 81%. This sprint does not target Objective 1 percentage movement because PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved, GitHub comment `3269642220` is only software-proof reply publication, and real vendor-sourced 2D LiDAR / ToF plus WAVE ROVER/UART/HIL materials remain missing.
4. Because O5 and O1 real materials are unavailable, this sprint targets the next actionable O2/O3/O4 evidence workflow rung: handoff from prior `field_evidence_real_material_response_review_decision` into field-owner next required evidence.

## Implementation Shape

Create a conservative review-handoff layer that consumes `field_evidence_real_material_response_review_decision` and emits:

- `schema=trashbot.field_evidence_real_material_response_review_handoff.v1`
- `summary.schema=trashbot.field_evidence_real_material_response_review_handoff_summary.v1`
- `capability=field_evidence_real_material_response_review_handoff`
- `evidence_boundary=software_proof_docker_field_evidence_real_material_response_review_handoff_gate`
- `source=software_proof`
- `status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`
- `prior_review_decision`
- `owner_handoff`
- `next_required_evidence`
- `missing_required_materials`
- `handoff_status`
- `blocked_reason`
- `rerun_or_backfill_guidance`
- `safe_copy` / `safe_phone_copy`

Allowed `handoff_status` values:

- `ready_for_field_owner_handoff_not_proven`
- `needs_material_backfill_handoff_not_proven`
- `rejected_unsafe_or_mixed_handoff_not_proven`
- `blocked_real_environment_unavailable_handoff_not_proven`
- `blocked_missing_review_decision_not_proven`

The implementation must reject or block unsafe wording around raw artifacts, credentials, local paths, ROS topics, `/cmd_vel`, serial/UART/WAVE ROVER details, checksums, tracebacks, delivery success, field pass, HIL, O5 external proof, true phone/browser proof, or control enablement.

## Owner File Ranges

Autonomy Algorithm Engineer may edit only:

- `pc-tools/evidence/field_evidence_real_material_response_review_handoff.py`
- `pc-tools/evidence/test_field_evidence_real_material_response_review_handoff.py`
- `docs/interfaces/evidence_contracts.md`

Robot Platform Engineer may edit only:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

User Touchpoint Full-Stack Engineer may edit only:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_response_review_handoff.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Hardware Infra Engineer is read-only by default:

- must read `docs/vendor/VENDOR_INDEX.md`
- may read cited local vendor files
- may read `docs/product/production_hardware_boundary.md`
- must not edit hardware config, vendor docs, product code, or sprint docs unless explicitly redirected

Product Manager / OKR Owner may edit closeout files only after worker validation:

- `sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/tech-done.md`
- `sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/side2side_check.md`
- `sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## Interface Boundary

The PC gate owns canonical artifact generation and can read only sanitized previous review-decision artifacts. It must not require real robot hardware, cloud credentials, live PR mutation, real phone, or external network proof.

Robot diagnostics owns summary-only consumption. It must expose a safe alias such as `robot_diagnostics_field_evidence_real_material_response_review_handoff_summary` without exposing raw handoff artifacts, raw review artifacts, low-level control details, credentials, local paths, or stack traces.

mobile/web owns presentation only. It may render handoff status, safe `evidence_ref`, owner handoff, next required evidence, missing materials, blocked reason, and safe copy. It must not send Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, review, material, rerun, or robot command requests from this panel.

Hardware consultation owns source-boundary facts only. `docs/vendor/VENDOR_INDEX.md` and local vendor files can support what hardware facts are source-bound, but they do not prove procurement, installation, wiring, calibration, UART feedback, WAVE ROVER HIL, or delivery success.

Product closeout owns evidence wording and OKR progress boundaries. It must not raise O5/O1/O2/O3/O4 percentages unless workers return real materials beyond Docker-local proof.

## Parallel Launch

Launch Autonomy, Robot, Full-Stack, and Hardware consultation in parallel because their file scopes are disjoint and Hardware is read-only. Product closeout starts only after those worker outputs are available.

Planned worker split:

- Autonomy: build the canonical gate and focused test.
- Robot: add diagnostics safe summary consumption.
- Full-Stack: add read-only mobile/web handoff panel and fixture.
- Hardware: verify that vendor/source boundary remains not-proven and no real hardware evidence arrived.

The main session should not implement product code or tests. It should dispatch workers with their role prompt, file scope, validation commands, and output requirements, then integrate their reported evidence into closeout docs.

## Validation Commands

Autonomy must run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/field_evidence_real_material_response_review_handoff.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_field_evidence_real_material_response_review_handoff.py
python3 pc-tools/evidence/field_evidence_real_material_response_review_handoff.py --help
rg -n "field_evidence_real_material_response_review_handoff|software_proof_docker_field_evidence_real_material_response_review_handoff_gate|ready_for_field_owner_handoff_not_proven|needs_material_backfill_handoff_not_proven|rejected_unsafe_or_mixed_handoff_not_proven|blocked_real_environment_unavailable_handoff_not_proven" pc-tools/evidence docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_real_material_response_review_handoff.py pc-tools/evidence/test_field_evidence_real_material_response_review_handoff.py docs/interfaces/evidence_contracts.md
```

Robot must run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary|field_evidence_real_material_response_review_handoff|software_proof_docker_field_evidence_real_material_response_review_handoff_gate" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

Full-Stack must run:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_response_review_handoff.json >/tmp/field_evidence_real_material_response_review_handoff_fixture.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "field_evidence_real_material_response_review_handoff|robot_diagnostics_field_evidence_real_material_response_review_handoff_summary|software_proof_docker_field_evidence_real_material_response_review_handoff_gate|ready_for_field_owner_handoff_not_proven" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_response_review_handoff.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Hardware consultation must run read-only checks:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "WAVE ROVER|UART|JSON|Orange Pi|LiDAR|ToF|vendor|PRRT_kwDOSWB9286CJ3tX" docs/vendor/VENDOR_INDEX.md docs/product/production_hardware_boundary.md OKR.md
```

Product closeout must run only after workers return:

```bash
test -f sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/tech-done.md
test -f sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/side2side_check.md
test -f sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/final.md
rg -n "field_evidence_real_material_response_review_handoff|software_proof_docker_field_evidence_real_material_response_review_handoff_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven|PRRT_kwDOSWB9286CJ3tX|3269642220" sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff OKR.md docs/process/okr_progress_log.md
```

Planning-doc acceptance for this Product Owner task:

```bash
test -f sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/pre_start.md
test -f sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/prd.md
test -f sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/tech-plan.md
rg -n "field_evidence_real_material_response_review_handoff|software_proof_docker_field_evidence_real_material_response_review_handoff_gate|OKR 最低优先级核对|PRRT_kwDOSWB9286CJ3tX|3269642220" sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff
git diff --check -- sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff
```

## Risks

- `ready_for_field_owner_handoff_not_proven` can be misread as field acceptance. UI and docs must state that it only means the next owner knows what to collect.
- The handoff must not widen into a control surface. Primary actions remain disabled.
- The summary must stay redacted and must not leak raw material payloads, local paths, credentials, ROS topics, serial/UART/WAVE ROVER details, checksums, tracebacks, or complete logs.
- O5 and O1 remain blocked until real external or hardware evidence arrives; no local handoff gate can move those percentages.
