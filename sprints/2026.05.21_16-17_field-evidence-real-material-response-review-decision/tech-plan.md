# Field Evidence Real Material Response Review Decision Tech Plan

Run time: 2026-05-21 16:03 CST

## Capability

- capability: `field_evidence_real_material_response_review_decision`
- evidence boundary: `software_proof_docker_field_evidence_real_material_response_review_decision_gate`
- sprint_type: epic
- planning owner: Product Manager / OKR Owner
- execution owners: Autonomy, Robot Platform, Full-Stack, Hardware consultation, Product closeout

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1 is Objective 5 at about 68%.
2. This sprint does not target Objective 5 percentage movement because real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/migration/cutover, production app/device, and true phone/browser evidence are still missing. Per the stop rule in `OKR.md` section 6, adding another local O5 metadata wrapper is not meaningful progress.
3. The next lowest Objective is Objective 1 at about 81%. This sprint does not target Objective 1 percentage movement because PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved, GitHub comment `3269642220` is only software-proof reply publication, and real vendor-sourced 2D LiDAR / ToF plus WAVE ROVER/UART/HIL materials remain missing.
4. Because O5 and O1 real materials are unavailable, this sprint targets the next actionable O2/O3/O4 evidence workflow rung: review-decision over the prior field-owner real-material response intake.

## Implementation Shape

Create a conservative review-decision layer that consumes `field_evidence_real_material_response_intake` and emits:

- `schema=trashbot.field_evidence_real_material_response_review_decision.v1`
- `summary.schema=trashbot.field_evidence_real_material_response_review_decision_summary.v1`
- `capability=field_evidence_real_material_response_review_decision`
- `evidence_boundary=software_proof_docker_field_evidence_real_material_response_review_decision_gate`
- `source=software_proof`
- `status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`
- `review_decision`
- `decision_reasons`
- `owner_handoff`
- `next_required_evidence`
- `blocked_claims`
- `safe_copy` / `safe_phone_copy`

Allowed `review_decision` values:

- `accepted_for_later_review_not_proven`
- `needs_material_backfill_not_proven`
- `rejected_unsafe_or_mixed_response_not_proven`
- `blocked_real_environment_unavailable_not_proven`
- `blocked_missing_field_evidence_real_material_response_intake_not_proven`

The implementation must reject or block unsafe wording around raw artifacts, credentials, local paths, ROS topics, `/cmd_vel`, serial/UART/WAVE ROVER details, checksums, tracebacks, delivery success, field pass, HIL, or control enablement.

## Owner File Ranges

Autonomy Algorithm Engineer may edit only:

- `pc-tools/evidence/field_evidence_real_material_response_review_decision.py`
- `pc-tools/evidence/test_field_evidence_real_material_response_review_decision.py`
- `docs/interfaces/evidence_contracts.md`

Robot Platform Engineer may edit only:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

User Touchpoint Full-Stack Engineer may edit only:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_response_review_decision.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Hardware Infra Engineer is read-only by default:

- must read `docs/vendor/VENDOR_INDEX.md`
- may read cited local vendor files
- must not edit hardware config, vendor docs, or product code unless explicitly redirected

Product Manager / OKR Owner may edit closeout files only after worker validation:

- `sprints/2026.05.21_16-17_field-evidence-real-material-response-review-decision/tech-done.md`
- `sprints/2026.05.21_16-17_field-evidence-real-material-response-review-decision/side2side_check.md`
- `sprints/2026.05.21_16-17_field-evidence-real-material-response-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## Validation Commands

Autonomy must run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/field_evidence_real_material_response_review_decision.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_field_evidence_real_material_response_review_decision.py
python3 pc-tools/evidence/field_evidence_real_material_response_review_decision.py --help
rg -n "field_evidence_real_material_response_review_decision|software_proof_docker_field_evidence_real_material_response_review_decision_gate|accepted_for_later_review_not_proven|needs_material_backfill_not_proven|rejected_unsafe_or_mixed_response_not_proven|blocked_real_environment_unavailable_not_proven" pc-tools/evidence docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_real_material_response_review_decision.py pc-tools/evidence/test_field_evidence_real_material_response_review_decision.py docs/interfaces/evidence_contracts.md
```

Robot must run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_real_material_response_review_decision_summary|field_evidence_real_material_response_review_decision|software_proof_docker_field_evidence_real_material_response_review_decision_gate" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

Full-Stack must run:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_response_review_decision.json >/tmp/field_evidence_real_material_response_review_decision_fixture.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "field_evidence_real_material_response_review_decision|robot_diagnostics_field_evidence_real_material_response_review_decision_summary|software_proof_docker_field_evidence_real_material_response_review_decision_gate|accepted_for_later_review_not_proven" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_response_review_decision.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Hardware consultation must run read-only checks:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "WAVE ROVER|UART|JSON|Orange Pi|LiDAR|ToF|vendor|PRRT_kwDOSWB9286CJ3tX" docs/vendor/VENDOR_INDEX.md docs/product/production_hardware_boundary.md OKR.md
```

Product closeout must run only after workers return:

```bash
test -f sprints/2026.05.21_16-17_field-evidence-real-material-response-review-decision/tech-done.md
test -f sprints/2026.05.21_16-17_field-evidence-real-material-response-review-decision/side2side_check.md
test -f sprints/2026.05.21_16-17_field-evidence-real-material-response-review-decision/final.md
rg -n "field_evidence_real_material_response_review_decision|software_proof_docker_field_evidence_real_material_response_review_decision_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven|PRRT_kwDOSWB9286CJ3tX|3269642220" sprints/2026.05.21_16-17_field-evidence-real-material-response-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.21_16-17_field-evidence-real-material-response-review-decision OKR.md docs/process/okr_progress_log.md
```

## Parallel Launch

Launch Autonomy, Robot, Full-Stack, and Hardware consultation in parallel because their write scopes are disjoint and the hardware task is read-only. Product closeout starts after their outputs are available.

## Risks

- This must not become a real-material acceptance claim. `accepted_for_later_review_not_proven` means review can continue later, not a field pass.
- Full-Stack must not enable Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, or robot commands from this panel.
- Robot diagnostics must not leak raw artifacts or hardware details.
- Hardware consultation must cite local vendor docs and keep all real hardware proof unresolved.
