# Field Evidence Rerun Execution Result Review Handoff Tech Plan

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff`
- Target capability: `field_evidence_rerun_execution_result_review_handoff`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate`
- Required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning status: ready for three parallel Engineer workers after Product planning.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1 is Objective 5 at about 68%. Objective 1 is about 81%; Objectives 2, 3, and 4 are about 99%.
2. This sprint does not target Objective 5 directly.
3. Reason: Objective 5 currently needs real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, production worker/cutover, or true phone/browser proof. This host has Docker only and the recent rules say not to repeat local O5 metadata depth without those materials.
4. Next lowest Objective 1 is also blocked on real hardware evidence. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending, and reply comment `3269642220` is not reviewer resolution. Required O1 evidence still includes real 2D LiDAR / ToF source or receipt, installation, wiring, power, calibration, HIL-entry, WAVE ROVER/UART/HIL, or reviewer resolution.
5. Chosen target: Objective 2/3/4 field-evidence follow-through via `field_evidence_rerun_execution_result_review_handoff`. The previous sprint completed `field_evidence_rerun_execution_result_review_decision`; this sprint converts that safe review decision into an owner handoff and real-material backfill request while preserving `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Evidence Inputs

- `AGENTS.md`: Epic sprint, parallel worker split, sprint documentation, Docker-only and evidence-boundary rules.
- `OKR.md` 4.1 and section 6: O5 and O1 blocker evidence, PR #5 unresolved status, and next actionable field-evidence route when real external/hardware materials are missing.
- `sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/final.md`: previous capability completed as `software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate`, not real field pass.
- GitHub PR evidence recorded in OKR and recent review context: `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved; `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending.
- `docs/product/mobile_user_flow.md` and `docs/product/elevator_assisted_delivery.md`: mobile and elevator field evidence panels stay read-only and fail-closed.

## Interface Impact

- Add canonical artifact schema: `trashbot.field_evidence_rerun_execution_result_review_handoff.v1`.
- Add canonical summary schema: `trashbot.field_evidence_rerun_execution_result_review_handoff_summary.v1`.
- Add Robot-safe alias: `robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary`.
- Add a mobile/web read-only panel that consumes the Robot-safe alias first and compatible safe fields second.
- No ROS topic, action, service, launch parameter, cloud endpoint, ACK/cursor, queue command, robot command, or hardware configuration may change.
- Existing Start Delivery, Confirm Dropoff, and Cancel gating must stay unchanged and fail-closed unless already enabled by existing independent safety gates.

## Worker 1: Autonomy Algorithm Engineer

Responsibility: PC gate and canonical review-handoff artifact.

Allowed file range:

- `pc-tools/evidence/field_evidence_rerun_execution_result_review_handoff.py`
- `tests/test_field_evidence_rerun_execution_result_review_handoff.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`
- `sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/tech-done.md` after implementation starts

Implementation requirements:

- Consume `trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1` or the compatible Robot-safe review-decision alias.
- Require same-safe-`evidence_ref`, `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Emit `trashbot.field_evidence_rerun_execution_result_review_handoff.v1` and `trashbot.field_evidence_rerun_execution_result_review_handoff_summary.v1`.
- Include source review decision, safe `evidence_ref`, owner handoff, blocker summary, next required real materials, reconciliation guidance, rerun guidance, safe copy, and the evidence boundary.
- Required real materials must name the field-owner backfill set: same-safe-`evidence_ref` task record, route/elevator runtime logs, route completion signal, elevator door/floor evidence, human assistance note, dropoff or cancel completion, delivery result, diagnostics/mobile safe summary, and true phone/browser evidence.
- Fail closed on raw artifact leakage, unsafe success/control copy, credentials, local paths, DB/queue URLs, OSS secrets, bearer tokens, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER, checksums, tracebacks, HIL/pass wording, O5 external proof claims, PR #5 resolution claims, PR #6 runtime claims, or delivery success claims.
- Any new technical comments must be Chinese and should explain why the handoff remains software proof and fail-closed.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_review_handoff.py
python3 -m unittest tests.test_field_evidence_rerun_execution_result_review_handoff
python3 pc-tools/evidence/field_evidence_rerun_execution_result_review_handoff.py --help
rg -n "field_evidence_rerun_execution_result_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate|owner_handoff|next_required_real_materials|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_review_handoff.py tests/test_field_evidence_rerun_execution_result_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff
```

## Worker 2: Robot Platform Engineer

Responsibility: diagnostics safe alias.

Allowed file range:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`
- `sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/tech-done.md` after implementation starts

Implementation requirements:

- Add `robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary`.
- Prefer the canonical review-handoff summary and reject unsafe raw review-decision or result packet material.
- Expose only source review decision, safe `evidence_ref`, owner handoff, blocker summary, next required real materials, reconciliation/rerun guidance, `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and the evidence boundary.
- Preserve existing diagnostics aliases and compatibility.
- Redact or omit raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, credentials, DB/queue URLs, OSS secrets, local paths, complete artifacts, checksums, traceback, HIL/pass wording, and delivery success claims.
- Any new technical comments must be Chinese and should explain the safety reason for exposing only the safe alias.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary|field_evidence_rerun_execution_result_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff
```

## Worker 3: User Touchpoint Full-Stack Engineer

Responsibility: mobile/web read-only panel.

Allowed file range:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_review_handoff.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/tech-done.md` after implementation starts

Implementation requirements:

- Add a read-only "现场证据复跑执行结果复核交接" panel.
- Prefer `robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary`; fall back only to compatible safe summary fields already present in status/diagnostics payloads.
- Show source review decision, safe `evidence_ref`, owner handoff, blocker summary, next required real materials, reconciliation/rerun guidance, evidence boundary, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Keep Start Delivery, Confirm Dropoff, and Cancel authorization unchanged and fail-closed.
- Never send Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, queue scheduling, execution scheduling, review submission, handoff submission, result submission, or robot command requests from this panel.
- Do not expose raw JSON, raw artifacts, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, tracebacks, checksums, or complete packets.
- Any new technical comments must be Chinese and should explain why the panel is read-only.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_review_handoff.json >/dev/null
rg -n "field_evidence_rerun_execution_result_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|现场证据复跑执行结果复核交接" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff
```

## Parallel Dispatch Requirements

- Start the three workers in parallel because their ownership boundaries are disjoint: Autonomy PC gate, Robot diagnostics alias, and Full-Stack mobile panel.
- The workers are not alone in the codebase and must not revert unrelated edits. Each worker must stay inside its allowed file range.
- Product should not implement code in the main session. Product only validates the returned evidence, updates sprint closeout docs, and conservatively updates `OKR.md` / progress log after implementation.

## Product Closeout Plan

Product closeout owns, after implementation only:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/tech-done.md`
- `sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/side2side_check.md`
- `sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/final.md`

Closeout requirements:

- Confirm all implementation docs under `docs/` were synchronized by responsible workers.
- Confirm Engineer comments in touched code are Chinese and preserve the required comment standard.
- Confirm no wording claims real field rerun, real Nav2/fixed-route runtime, real route/elevator field pass, HIL, Objective 5 external proof, true phone/browser proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved, PR #6 runtime proof, dropoff/cancel completion, delivery result, or delivery success.
- Update OKR and progress log conservatively if implementation proceeds. Do not raise Objective 5 or Objective 1 unless real evidence appears.
- Do not create `tech-done.md`, `side2side_check.md`, or `final.md` during the planning-only step.

Product acceptance commands after implementation:

```bash
test -f sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/tech-done.md
test -f sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/side2side_check.md
test -f sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/final.md
rg -n "field_evidence_rerun_execution_result_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|PR #6" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff
```

## Planning-only Validation Commands

The Product planning step must run:

```bash
test -f sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/pre_start.md
test -f sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/prd.md
test -f sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff/tech-plan.md
rg -n "field_evidence_rerun_execution_result_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate|OKR 最低优先级核对|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|delivery_success=false|primary_actions_enabled=false|not_proven" sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff
git diff --check -- sprints/2026.05.21_09-10_field-evidence-rerun-execution-result-review-handoff
```

## Boundaries And Non Claims

This sprint must not claim real field rerun, real task record, real Nav2/fixed-route runtime, real route completion signal, real elevator door/floor/human assistance proof, real route/elevator field pass, real phone/browser validation, real PWA prompt/userChoice, WAVE ROVER/UART/HIL, delivery success, dropoff completion, cancel completion, Objective 5 external proof, public HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live traffic proof, production DB/queue or worker/cutover proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved, or PR #6 runtime proof.
