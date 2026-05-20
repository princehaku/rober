# Field Evidence Rerun Execution Callback Review Handoff Tech Plan

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff`
- Target capability: `field_evidence_rerun_execution_callback_review_handoff`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate`
- Required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning status: ready for three parallel Engineer workers after Product planning.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5 is about 68%, below Objective 1 at about 81% and Objectives 2/3/4 at about 99%.
2. This sprint is not targeting Objective 5 directly.
3. Reason: Objective 5 currently needs real external proof unavailable on this Docker-only host: real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser external proof. Recent O5 local guards already covered metadata/software-proof failure visibility, so another local O5 blocker wrapper would repeat the same blocker.
4. Next lowest Objective 1 is about 81%, but PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / material pending despite PR #5 being merged and conservative reply comment id `3269642220` existing. This host still lacks WAVE ROVER/UART/HIL and real 2D LiDAR / ToF vendor/source/procurement/install/calibration materials.
5. PR #6 is README/docs-only and has no review threads; it is not runtime, hardware, HIL, true phone/browser, or O5 external proof.
6. Chosen target: O2/O3/O4 `field_evidence_rerun_execution_callback_review_handoff`, because the previous sprint final says the next useful action needs real same-safe-`evidence_ref` materials, and absent those materials only a bounded software-proof handoff/reconciliation rung is valid.

## Evidence Inputs

- `OKR.md` 4.1 current snapshot.
- Previous sprint final: `sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision/final.md`.
- PR #5 thread state: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false`.
- PR #6 boundary: README/docs-only, no review threads, no runtime/hardware/HIL/phone/browser/O5 external proof.
- Mobile user flow boundary: mobile panels must remain read-only, phone-safe, and fail-closed for primary actions.

## Worker 1: Autonomy Algorithm Engineer

Responsibility: PC gate and canonical handoff artifact.

Allowed file range:

- `pc-tools/evidence/field_evidence_rerun_execution_callback_review_handoff.py`
- `tests/test_field_evidence_rerun_execution_callback_review_handoff.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Consume `field_evidence_rerun_execution_callback_review_decision` artifact/summary or Robot safe alias.
- Validate source schema, boundary, review decision, same-safe-`evidence_ref`, and preserved false states.
- Produce `trashbot.field_evidence_rerun_execution_callback_review_handoff.v1` and `trashbot.field_evidence_rerun_execution_callback_review_handoff_summary.v1`.
- Output owner handoff, next required evidence, rerun guidance, reconciliation guidance, blocker summary, and `safe_copy`.
- Preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and `software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate`.
- Fail closed on raw artifact wrappers, unsafe copy, success/control wording, path/credential/ROS topic/serial/UART/WAVE ROVER/checksum/traceback leakage, true field pass, delivery success, HIL, O5 external proof, or PR #5 resolution claims.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_callback_review_handoff.py
python3 -m unittest tests.test_field_evidence_rerun_execution_callback_review_handoff
python3 pc-tools/evidence/field_evidence_rerun_execution_callback_review_handoff.py --help
rg -n "field_evidence_rerun_execution_callback_review_handoff|software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence tests pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_callback_review_handoff.py tests/test_field_evidence_rerun_execution_callback_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff
```

## Worker 2: Robot Platform Engineer

Responsibility: diagnostics safe alias.

Allowed file range:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add `robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary`.
- Prefer canonical handoff summary and reject unsafe raw callback/review/handoff material.
- Expose only owner handoff, next required evidence, rerun guidance, reconciliation guidance, blocker summary, safe `evidence_ref`, preserved false states, `not_proven`, and evidence boundary.
- Redact or omit raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, credentials, local paths, complete artifacts, checksums, traceback, HIL/pass wording, and delivery success claims.
- Preserve existing diagnostics aliases and compatibility.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary|field_evidence_rerun_execution_callback_review_handoff|software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff
```

## Worker 3: User Touchpoint Full-Stack Engineer

Responsibility: mobile/web read-only panel.

Allowed file range:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add a read-only "现场证据复跑执行回执复核交接" panel.
- Prefer `robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary`; fall back only to safe compatible summary fields already present in status/diagnostics payloads.
- Show safe `evidence_ref`, owner handoff, next required evidence, rerun guidance, reconciliation guidance, blocker summary, evidence boundary, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Never send Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, queue scheduling, execution scheduling, callback submission, review submission, handoff submission, or robot command requests from the panel.
- Keep existing Start Delivery, Confirm Dropoff, and Cancel gating unchanged and fail-closed.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "field_evidence_rerun_execution_callback_review_handoff|software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|现场证据复跑执行回执复核交接" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff
```

## Product Closeout Plan

Product closeout owns:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/tech-done.md`
- `sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/side2side_check.md`
- `sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/final.md`

Closeout requirements:

- Confirm all implementation docs under `docs/` were synchronized by the responsible workers.
- Confirm no wording claims real field rerun, real Nav2, real route/elevator field pass, HIL, O5 external proof, true phone/browser proof, PR #5 resolved, dropoff/cancel completion, cancel completion, delivery result, or delivery success.
- Update OKR and progress log conservatively if implementation proceeds. Do not raise Objective 5 or Objective 1 unless real evidence appears.

Product acceptance commands after implementation:

```bash
test -f sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/tech-done.md
test -f sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/side2side_check.md
test -f sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/final.md
rg -n "field_evidence_rerun_execution_callback_review_handoff|software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|PR #6" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff
```

## Planning-only Validation Commands

The Product planning step must run:

```bash
test -f sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/pre_start.md
test -f sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/prd.md
test -f sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/tech-plan.md
rg -n "field_evidence_rerun_execution_callback_review_handoff|software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|OKR 最低优先级核对|PRRT_kwDOSWB9286CJ3tX|PR #6" sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff
git diff --check -- sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff
```

## Boundaries And Non-claims

This sprint must not claim real field rerun, real Nav2, real route/elevator field pass, real task record generation, real route completion signal generation, real elevator door/floor/human assistance proof, real phone/browser validation, real PWA prompt/userChoice, WAVE ROVER/UART/HIL, delivery success, dropoff completion, cancel completion, O5 external proof, public HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live traffic proof, production DB/queue or worker/cutover proof, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved.
