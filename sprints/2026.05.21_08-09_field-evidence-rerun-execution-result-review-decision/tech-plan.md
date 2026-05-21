# Field Evidence Rerun Execution Result Review Decision Tech Plan

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision`
- Target capability: `field_evidence_rerun_execution_result_review_decision`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate`
- Required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning status: ready for three parallel Engineer workers after Product planning.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1 is Objective 5 at about 68%. Objective 1 is about 81%; Objectives 2, 3, and 4 are about 99%.
2. This sprint does not target Objective 5 directly.
3. Reason: `OKR.md` section 6 says not to repeat local O5 metadata depth unless at least one real external material exists: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, production worker/cutover, or true phone/browser evidence. This host has Docker only and none of those materials.
4. Next lowest Objective 1 still depends on real hardware material. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / material pending; comment `3269642220` is not reviewer resolution. PR #6 is README/docs-only and does not provide runtime, hardware, HIL, phone/browser, or O5 external proof.
5. Chosen target: `field_evidence_rerun_execution_result_review_decision` in the Objective 2/3/4 field-evidence chain. The previous sprint completed `field_evidence_rerun_execution_result_intake`, and its next gate points here when status is `accepted`. This keeps progress software-proof and fail-closed while the real field materials remain absent.

## Evidence Inputs

- `AGENTS.md`: Epic sprint, parallel worker split, sprint documentation, evidence-boundary, and Docker-only hardware limits.
- `OKR.md` 4.1 and section 6: Objective 5/O1 blocker and next actionable Objective 2/3/4 evidence chain.
- `sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/final.md`: previous capability completed with `software_proof_docker_field_evidence_rerun_execution_result_intake_gate`, not real field pass or delivery success.
- `sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/tech-plan.md`: accepted result intake should advance to `field_evidence_rerun_execution_result_review_decision`.
- Product mobile flow: phone surfaces remain read-only and fail-closed for evidence review panels.

## Interface Impact

- Add a new canonical summary schema proposal: `trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1`.
- Add a new Robot-safe alias: `robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary`.
- Add a mobile/web read-only panel that consumes the Robot-safe alias first and compatible safe fields second.
- No ROS topic, action, service, launch parameter, cloud endpoint, ACK/cursor, queue command, or hardware configuration may change in this sprint.
- Existing Start Delivery, Confirm Dropoff, and Cancel gating must stay unchanged and disabled unless existing safety gates independently allow them.

## Worker 1: Autonomy Algorithm Engineer

Responsibility: PC gate and canonical review-decision artifact.

Allowed file range:

- `pc-tools/evidence/field_evidence_rerun_execution_result_review_decision.py`
- `tests/test_field_evidence_rerun_execution_result_review_decision.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`
- `sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/tech-done.md` after implementation starts

Implementation requirements:

- Consume `trashbot.field_evidence_rerun_execution_result_intake_summary.v1` or a Robot-safe compatible alias.
- Require same-safe-`evidence_ref`, `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Only `result_intake_status=accepted` may produce a reviewable decision path; `missing`, `rejected`, or `blocked` must become `needs_material_backfill` or `blocked`.
- Emit `trashbot.field_evidence_rerun_execution_result_review_decision.v1` and `trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1`.
- Decision values: `accepted_for_review`, `needs_material_backfill`, `rejected`, `blocked`.
- Include safe `evidence_ref`, intake reference, decision, blocker/rejection/backfill reason, next required evidence, owner handoff, reconciliation hint, safe copy, and the evidence boundary.
- Fail closed on raw artifact leakage, unsafe success/control copy, credentials, local paths, DB/queue URLs, OSS secrets, bearer tokens, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER, checksums, tracebacks, HIL/pass wording, O5 external proof claims, PR #5 resolution claims, PR #6 runtime claims, or delivery success claims.
- Any new technical comments must be Chinese and should explain why unsafe evidence is rejected.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_review_decision.py
python3 -m unittest tests.test_field_evidence_rerun_execution_result_review_decision
python3 pc-tools/evidence/field_evidence_rerun_execution_result_review_decision.py --help
rg -n "field_evidence_rerun_execution_result_review_decision|software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate|accepted_for_review|needs_material_backfill|rejected|blocked|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_review_decision.py tests/test_field_evidence_rerun_execution_result_review_decision.py pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision
```

## Worker 2: Robot Platform Engineer

Responsibility: diagnostics safe alias.

Allowed file range:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`
- `sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/tech-done.md` after implementation starts

Implementation requirements:

- Add `robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary`.
- Prefer the canonical review-decision summary and reject unsafe raw review/result packet material.
- Expose only decision, safe `evidence_ref`, intake reference, blocker/rejection/backfill reason, next required evidence, owner handoff, `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and the evidence boundary.
- Preserve existing diagnostics aliases and compatibility.
- Redact or omit raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, credentials, DB/queue URLs, OSS secrets, local paths, complete artifacts, checksums, traceback, HIL/pass wording, and delivery success claims.
- Any new technical comments must be Chinese and should explain the safety reason for redaction.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary|field_evidence_rerun_execution_result_review_decision|software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision
```

## Worker 3: User Touchpoint Full-Stack Engineer

Responsibility: mobile/web read-only panel.

Allowed file range:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_review_decision.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/tech-done.md` after implementation starts

Implementation requirements:

- Add a read-only "现场证据复跑执行结果复核决策" panel.
- Prefer `robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary`; fall back only to compatible safe summary fields already present in status/diagnostics payloads.
- Show safe `evidence_ref`, decision, intake reference, blocker/rejection/backfill reason, next required evidence, owner handoff, evidence boundary, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Keep Start Delivery, Confirm Dropoff, and Cancel authorization unchanged and fail-closed.
- Never send Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, queue scheduling, execution scheduling, review submission, handoff submission, result submission, or robot command requests from this panel.
- Do not expose raw JSON, raw artifacts, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, tracebacks, checksums, or complete packets.
- Any new technical comments must be Chinese and should explain why the panel is read-only.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_review_decision.json >/dev/null
rg -n "field_evidence_rerun_execution_result_review_decision|software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|现场证据复跑执行结果复核决策" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision
```

## Product Closeout Plan

Product closeout owns, after implementation only:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/tech-done.md`
- `sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/side2side_check.md`
- `sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/final.md`

Closeout requirements:

- Confirm all implementation docs under `docs/` were synchronized by the responsible workers.
- Confirm Engineer comments in touched code are Chinese and preserve the required comment standard.
- Confirm no wording claims real field rerun, real Nav2/fixed-route runtime, real route/elevator field pass, HIL, O5 external proof, true phone/browser proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved, PR #6 runtime proof, dropoff/cancel completion, delivery result, or delivery success.
- Update OKR and progress log conservatively if implementation proceeds. Do not raise Objective 5 or Objective 1 unless real evidence appears.
- Do not create `tech-done.md`, `side2side_check.md`, or `final.md` during the planning-only step.

Product acceptance commands after implementation:

```bash
test -f sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/tech-done.md
test -f sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/side2side_check.md
test -f sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/final.md
rg -n "field_evidence_rerun_execution_result_review_decision|software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|PR #6" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision
```

## Planning-only Validation Commands

The Product planning step must run:

```bash
test -f sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/pre_start.md
test -f sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/prd.md
test -f sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/tech-plan.md
rg -n "sprint_type: epic|field_evidence_rerun_execution_result_review_decision|OKR 最低优先级核对|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision
git diff --check -- sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision
```

## Boundaries And Non-claims

This sprint must not claim real field rerun, real task record, real Nav2/fixed-route runtime, real route completion signal, real elevator door/floor/human assistance proof, real route/elevator field pass, real phone/browser validation, real PWA prompt/userChoice, WAVE ROVER/UART/HIL, delivery success, dropoff completion, cancel completion, O5 external proof, public HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live traffic proof, production DB/queue or worker/cutover proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved, or PR #6 runtime proof.
