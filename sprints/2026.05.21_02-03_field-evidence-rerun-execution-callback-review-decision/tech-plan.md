# Field Evidence Rerun Execution Callback Review Decision Tech Plan

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision`
- Target capability: `field_evidence_rerun_execution_callback_review_decision`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate`
- Required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning status: ready for three parallel Engineer workers.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5 is about 68%, lower than Objective 1 at about 81% and Objectives 2/3/4 at about 99%.
2. This sprint is not targeting Objective 5 directly.
3. Reason: Objective 5 currently needs real external proof unavailable on this Docker-only host: real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser external proof. Recent local O5 guards already covered auth failure, media degradation, command sequence regression, and stale status as software proof; repeating another local O5 metadata rung without fresh user value would consume the same blocker.
4. Next lowest Objective 1 is about 81%, but PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending and the previous hardware callback review handoff already consumed the local wrapper path. This host still lacks WAVE ROVER/UART/HIL and real 2D LiDAR / ToF materials.
5. Chosen target: O2/O3/O4 `field_evidence_rerun_execution_callback_review_decision`, because the previous sprint explicitly ended with callback intake and identified review decision as the next executable rung.

## Evidence Inputs

- `OKR.md` 4.1 current snapshot.
- PR #5 review threads: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, `PRRT_kwDOSWB9286CJ3tX` unresolved / vendor-source material pending.
- PR #6: README/docs-only; no runtime, hardware, HIL, true phone/browser, or O5 external proof.
- Previous sprint: `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/final.md` says the next rung is `field_evidence_rerun_execution_callback_review_decision`.
- Existing pattern: `field_evidence_rerun_callback_review_decision` and other review-decision gates already use metadata-only fail-closed review semantics.

## Worker 1: Autonomy Algorithm Engineer

Responsibility: PC gate and canonical review-decision artifact.

Allowed file range:

- `pc-tools/evidence/field_evidence_rerun_execution_callback_review_decision.py`
- `tests/test_field_evidence_rerun_execution_callback_review_decision.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Consume `field_evidence_rerun_execution_callback_intake` artifact/summary or Robot safe alias.
- Validate source schema/boundary/status and preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Produce `review_decision` values for ready, missing, rejected, blocked, unsupported, unsafe, evidence-ref mismatch, and source-not-ready cases.
- Keep accepted/missing/rejected/blocked material groups visible only as safe metadata.
- Generate `decision_reasons`, `owner_handoff`, `next_required_evidence`, `rerun_guidance`, and `safe_copy`.
- Fail closed on raw artifact wrappers, unsafe copy, success/control wording, path/credential/ROS topic/serial/UART/WAVE ROVER/checksum/traceback leakage, or any true field-pass/delivery/HIL/O5 claim.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_callback_review_decision.py
python3 -m unittest tests.test_field_evidence_rerun_execution_callback_review_decision
python3 pc-tools/evidence/field_evidence_rerun_execution_callback_review_decision.py --help
rg -n "field_evidence_rerun_execution_callback_review_decision|software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence tests pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_callback_review_decision.py tests/test_field_evidence_rerun_execution_callback_review_decision.py pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision
```

## Worker 2: Robot Platform Engineer

Responsibility: diagnostics safe alias.

Allowed file range:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add `robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary`.
- Prefer canonical review-decision summary and reject raw callback-intake/review material when it contains unsafe fields.
- Redact or omit raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, credentials, local paths, complete artifacts, checksums, traceback, HIL/pass wording, and delivery success claims.
- Preserve `software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate`.
- Keep existing diagnostics aliases backward compatible.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary|field_evidence_rerun_execution_callback_review_decision|software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision
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

- Add a read-only "现场证据复跑执行回执复核决策" panel.
- Prefer `robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary`; fall back only to safe compatible summary fields already present in status/diagnostics payloads.
- Show safe `evidence_ref`, review decision, decision reasons, accepted/missing/rejected/blocked materials, owner handoff, next required evidence, evidence boundary, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Never send Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, queue scheduling, execution scheduling, callback submission, review submission, or robot command requests from the panel.
- Keep existing Start Delivery, Confirm Dropoff, and Cancel gating unchanged.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
rg -n "field_evidence_rerun_execution_callback_review_decision|software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|现场证据复跑执行回执复核决策" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision
```

## Product Closeout Plan

Product closeout owns:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision/tech-done.md`
- `sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision/side2side_check.md`
- `sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision/final.md`

Closeout requirements:

- Confirm all engineering docs under `docs/` were synchronized.
- Confirm no wording claims real现场复跑、真实 Nav2、真实 route/elevator field pass、HIL、O5 external proof、真实 phone/browser proof、PR #5 resolved, dropoff/cancel completion, cancel completion, delivery result, or delivery success.
- Update OKR and progress log conservatively. Do not raise Objective 5 or Objective 1 unless real evidence appears.

Product acceptance commands:

```bash
test -f sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision/tech-done.md
test -f sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision/side2side_check.md
test -f sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision/final.md
rg -n "field_evidence_rerun_execution_callback_review_decision|software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|PR #6" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision
```

## Boundaries And Non-claims

This sprint must not claim real field rerun, real Nav2, real route/elevator field pass, real task record generation, real route completion signal generation, real elevator door/floor/human assistance proof, real phone/browser validation, real PWA prompt/userChoice, WAVE ROVER/UART/HIL, delivery success, dropoff completion, cancel completion, O5 external proof, public HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live traffic proof, production DB/queue or worker/cutover proof, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved.
