# Field Evidence Rerun Execution Result Intake Tech Plan

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_07-08_field-evidence-rerun-execution-result-intake`
- Target capability: `field_evidence_rerun_execution_result_intake`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_intake_gate`
- Required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning status: ready for three parallel Engineer workers after Product planning.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5 is about 68%, below Objective 1 at about 81% and Objectives 2/3/4 at about 99%.
2. This sprint is not targeting Objective 5 directly.
3. Reason: latest O5 final `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/final.md` says local O5 guard work must not continue without real external materials or a fresh unguarded failure mode. This Docker-only host still lacks real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, and true phone/browser external proof.
4. Next lowest Objective 1 is about 81%, but PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved. PR #6 is README/docs-only and is not runtime, hardware, HIL, phone/browser, or O5 external proof.
5. Chosen target: O2/O3/O4 `field_evidence_rerun_execution_result_intake`, because latest related sprint `field_evidence_rerun_execution_callback_review_handoff` says the next useful action needs real same-safe-`evidence_ref` field materials. Since those materials are absent on this host, the valid software-proof step is a bounded result packet intake that records `missing` / `accepted` / `rejected` / `blocked` without claiming field success.

## Evidence Inputs

- `OKR.md` 4.1 current snapshot.
- Latest O5 blocker final: `sprints/2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard/final.md`.
- Latest field-evidence final: `sprints/2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff/final.md`.
- PR #5 thread state: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`.
- PR #6 boundary: README/docs-only, no runtime/hardware/HIL/phone/browser/O5 external proof.
- Mobile user flow boundary: mobile panels must remain read-only, phone-safe, and fail-closed for primary actions.

## Worker 1: Autonomy Algorithm Engineer

Responsibility: PC gate and canonical result-intake artifact.

Allowed file range:

- `pc-tools/evidence/field_evidence_rerun_execution_result_intake.py`
- `tests/test_field_evidence_rerun_execution_result_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Consume `field_evidence_rerun_execution_callback_review_handoff` artifact/summary or Robot safe alias.
- Optionally consume an owner-safe execution result packet that contains only sanitized packet state and material summary.
- Validate source schema, evidence boundary, same-safe-`evidence_ref`, preserved false states, and result packet state.
- Produce `trashbot.field_evidence_rerun_execution_result_intake.v1` and `trashbot.field_evidence_rerun_execution_result_intake_summary.v1`.
- Result intake status must be one of `missing`, `accepted`, `rejected`, or `blocked`; `accepted` means only accepted for review intake, not field pass.
- Output owner handoff, result packet summary, missing/rejected/blocked reasons, next required evidence, reconciliation hint, and `safe_copy`.
- Preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and `software_proof_docker_field_evidence_rerun_execution_result_intake_gate`.
- Fail closed on raw artifacts, unsafe copy, success/control wording, path/credential/DB/queue URL/ROS topic/serial/UART/WAVE ROVER/checksum/traceback leakage, true field pass, delivery success, HIL, O5 external proof, PR #5 resolution claims, or PR #6 runtime claims.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_intake.py
python3 -m unittest tests.test_field_evidence_rerun_execution_result_intake
python3 pc-tools/evidence/field_evidence_rerun_execution_result_intake.py --help
rg -n "field_evidence_rerun_execution_result_intake|software_proof_docker_field_evidence_rerun_execution_result_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|missing|accepted|rejected|blocked" pc-tools/evidence tests pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_intake.py tests/test_field_evidence_rerun_execution_result_intake.py pc-tools/README.md docs/interfaces/evidence_contracts.md sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake
```

## Worker 2: Robot Platform Engineer

Responsibility: diagnostics safe alias.

Allowed file range:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add `robot_diagnostics_field_evidence_rerun_execution_result_intake_summary`.
- Prefer canonical result-intake summary and reject unsafe raw result packet material.
- Expose only result intake status, safe `evidence_ref`, owner handoff, missing/rejected/blocked reasons, next required evidence, preserved false states, `not_proven`, and evidence boundary.
- Redact or omit raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, credentials, DB/queue URLs, OSS secrets, local paths, complete artifacts, checksums, traceback, HIL/pass wording, and delivery success claims.
- Preserve existing diagnostics aliases and compatibility.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_execution_result_intake_summary|field_evidence_rerun_execution_result_intake|software_proof_docker_field_evidence_rerun_execution_result_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake
```

## Worker 3: User Touchpoint Full-Stack Engineer

Responsibility: mobile/web read-only panel.

Allowed file range:

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_intake.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- current sprint implementation docs after code lands

Implementation requirements:

- Add a read-only "现场证据复跑执行结果回填" panel.
- Prefer `robot_diagnostics_field_evidence_rerun_execution_result_intake_summary`; fall back only to safe compatible summary fields already present in status/diagnostics payloads.
- Show safe `evidence_ref`, result intake status, owner handoff, missing/rejected/blocked reasons, next required evidence, evidence boundary, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Never send Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, queue scheduling, execution scheduling, callback submission, review submission, handoff submission, result submission, or robot command requests from the panel.
- Keep existing Start Delivery, Confirm Dropoff, and Cancel gating unchanged and fail-closed.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_intake.json >/dev/null
rg -n "field_evidence_rerun_execution_result_intake|software_proof_docker_field_evidence_rerun_execution_result_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|现场证据复跑执行结果回填" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake
```

## Product Closeout Plan

Product closeout owns, after implementation only:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/tech-done.md`
- `sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/side2side_check.md`
- `sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/final.md`

Closeout requirements:

- Confirm all implementation docs under `docs/` were synchronized by the responsible workers.
- Confirm no wording claims real field rerun, real Nav2, real route/elevator field pass, HIL, O5 external proof, true phone/browser proof, PR #5 resolved, PR #6 runtime proof, dropoff/cancel completion, delivery result, or delivery success.
- Update OKR and progress log conservatively if implementation proceeds. Do not raise Objective 5 or Objective 1 unless real evidence appears.
- Do not create `tech-done.md`, `side2side_check.md`, or `final.md` during the planning-only step.

Product acceptance commands after implementation:

```bash
test -f sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/tech-done.md
test -f sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/side2side_check.md
test -f sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/final.md
rg -n "field_evidence_rerun_execution_result_intake|software_proof_docker_field_evidence_rerun_execution_result_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|PR #6" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake
```

## Planning-only Validation Commands

The Product planning step must run:

```bash
test -f sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/pre_start.md
test -f sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/prd.md
test -f sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/tech-plan.md
rg -n "field_evidence_rerun_execution_result_intake|software_proof_docker_field_evidence_rerun_execution_result_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|OKR 最低优先级核对|PRRT_kwDOSWB9286CJ3tX|PR #6" sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake
git diff --check -- sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake
```

## Boundaries And Non-claims

This sprint must not claim real field rerun, real Nav2, real route/elevator field pass, real task record generation, real route completion signal generation, real elevator door/floor/human assistance proof, real phone/browser validation, real PWA prompt/userChoice, WAVE ROVER/UART/HIL, delivery success, dropoff completion, cancel completion, O5 external proof, public HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live traffic proof, production DB/queue or worker/cutover proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved, or PR #6 runtime proof.
