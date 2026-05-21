# Field Evidence Rerun Execution Result Acceptance Packet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or the repo-required Codex worker flow. Steps use checkbox (`- [ ]`) syntax for tracking. Main session must dispatch Engineer workers; main session must not directly edit product code, tests, hardware config, or runtime implementation.

**Goal:** Build `field_evidence_rerun_execution_result_acceptance_packet` so field owners can evaluate whether same-safe-`evidence_ref` execution materials are ready for acceptance review while preserving `software_proof/not_proven`.

**Architecture:** Autonomy owns the PC evidence gate and schema. Robot owns the safe diagnostics alias. Full-Stack owns the read-only mobile panel. Product owns closeout and OKR conservatism after Engineer evidence is returned.

**Tech Stack:** Python evidence tooling, ROS2 behavior diagnostics, dependency-free `mobile/web`, Python `unittest`, Node syntax check, Markdown sprint/product/interface docs.

---

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5, about 68%.
2. Next lowest Objective: Objective 1, about 81%.
3. This sprint does not directly target Objective 5 because the 2026.05.21 10-11 final says not to add another local O5 wrapper unless real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or true phone/browser proof appears.
4. This sprint does not directly target Objective 1 because PR #5 `PRRT_kwDOSWB9286CJ3tX` is still unresolved / `is_resolved=false` / material pending, and comment `3269642220` is only a software-proof reply, not reviewer resolution.
5. This sprint targets the next actionable Objective 2 / Objective 3 / Objective 4 field-evidence family by advancing `field_evidence_rerun_execution_result_review_handoff` into `field_evidence_rerun_execution_result_acceptance_packet`.
6. Expected OKR percentage movement: none during software-proof implementation. Any final closeout must preserve `software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## File Structure And Ownership

### Worker 1: Autonomy Algorithm Engineer

Allowed files:

- `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_packet.py`
- `tests/test_field_evidence_rerun_execution_result_acceptance_packet.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`
- this sprint's `tech-done.md` section for Autonomy evidence only, if Product asks for worker-side evidence append

Responsibility:

- Create a PC evidence gate for `field_evidence_rerun_execution_result_acceptance_packet`.
- Define schemas `trashbot.field_evidence_rerun_execution_result_acceptance_packet.v1` and `trashbot.field_evidence_rerun_execution_result_acceptance_packet_summary.v1`.
- Require the same safe `evidence_ref` across real task record, Nav2/fixed-route runtime log, route completion signal, elevator evidence, dropoff/cancel completion, delivery result, true phone/browser evidence, and diagnostics/mobile safe summary.
- Return conservative verdicts such as `ready_for_field_owner_acceptance_review_not_proven`, `needs_material_backfill`, `blocked_evidence_ref_mismatch`, `blocked_unsafe_material`, and `rejected_success_claim`.
- Reject any local material that tries to claim `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true`.

Validation commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_packet.py
python3 -m unittest tests.test_field_evidence_rerun_execution_result_acceptance_packet
python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_packet.py --help
rg -n "field_evidence_rerun_execution_result_acceptance_packet|software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate|same_evidence_ref|required_materials|task record|Nav2|fixed-route|route completion signal|elevator evidence|dropoff|cancel|delivery result|true phone|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence tests pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence tests pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Worker 2: Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`
- this sprint's `tech-done.md` section for Robot evidence only, if Product asks for worker-side evidence append

Responsibility:

- Add `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary`.
- Consume only the canonical Autonomy safe summary, not raw task records, raw logs, raw route/elevator artifacts, or complete acceptance packets.
- Preserve redaction: no ROS topics, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER details, credentials, DB/queue URLs, tracebacks, complete artifacts, checksums, raw diagnostics, or success/control claims.
- Keep `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.

Validation commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary|field_evidence_rerun_execution_result_acceptance_packet|software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX|3269642220" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md
```

### Worker 3: User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- this sprint's `tech-done.md` section for Full-Stack evidence only, if Product asks for worker-side evidence append

Responsibility:

- Add a read-only mobile/web panel for `field_evidence_rerun_execution_result_acceptance_packet`.
- Show packet verdict, safe `evidence_ref`, missing materials, accepted materials, blocked materials, owner next steps, and proof boundary.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not add fetches for raw diagnostics, raw artifacts, ACK/cursor requests, command replay, automatic resubmit, or robot-control endpoints.
- Use Chinese-first copy for field owner/support clarity.

Validation commands:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet.json >/tmp/field_evidence_acceptance_packet_fixture_check.json
rg -n "field_evidence_rerun_execution_result_acceptance_packet|software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate|现场证据复跑执行结果验收包|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven|Start Delivery|Confirm Dropoff|Cancel|true phone/browser" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web docs/product/mobile_user_flow.md
```

### Worker 4: Product Manager / OKR Owner

Allowed files after Engineer implementation:

- `sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-done.md`
- `sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/side2side_check.md`
- `sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Responsibility:

- Verify Engineer evidence before closeout.
- Preserve Objective 5 at about 68% and Objective 1 at about 81% unless real materials appear.
- State that PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved and comment `3269642220` is not reviewer resolution.
- State that `field_evidence_rerun_execution_result_acceptance_packet` is acceptance readiness only, not real route/elevator field pass, not delivery result, and not delivery success.

Validation commands:

```bash
test -f sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-done.md
test -f sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/side2side_check.md
test -f sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/final.md
rg -n "field_evidence_rerun_execution_result_acceptance_packet|software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not delivery success|true phone/browser" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet
```

## Parallel Dispatch Plan

- Dispatch Worker 1, Worker 2, and Worker 3 in parallel only if their write scopes stay disjoint and the acceptance-packet summary field name is frozen as `field_evidence_rerun_execution_result_acceptance_packet`.
- Worker 1 owns canonical schema and verdict semantics.
- Worker 2 may proceed against the planned safe summary contract but must adapt if Worker 1 returns a schema correction.
- Worker 3 may proceed against the planned fixture contract but must adapt if Worker 1 or Worker 2 returns a safer field shape.
- Worker 4 runs only after Engineer evidence is returned.

## Required Guard Semantics

All implementation outputs must converge on these semantics:

```text
capability=field_evidence_rerun_execution_result_acceptance_packet
proof_boundary=software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate
source=software_proof
not_proven
safe_to_control=false
delivery_success=false
primary_actions_enabled=false
same_evidence_ref_required=true
required_materials=task_record,nav2_fixed_route_runtime_log,route_completion_signal,elevator_evidence,dropoff_cancel_completion,delivery_result,true_phone_browser_evidence,diagnostics_mobile_safe_summary
```

Allowed verdicts:

- `ready_for_field_owner_acceptance_review_not_proven`
- `needs_material_backfill`
- `blocked_evidence_ref_mismatch`
- `blocked_unsafe_material`
- `rejected_success_claim`
- `blocked_missing_acceptance_packet`

Forbidden behavior:

- Do not claim `delivery_success=true`.
- Do not enable Start Delivery, Confirm Dropoff, or Cancel.
- Do not expose raw artifacts, secrets, ROS topics, `/cmd_vel`, UART/serial/WAVE ROVER details, DB/queue URLs, tracebacks, complete artifacts, checksums, or raw diagnostics.
- Do not resolve or imply resolution of PR #5 `PRRT_kwDOSWB9286CJ3tX`.
- Do not treat comment `3269642220` as reviewer resolution.

## Acceptance Checklist

- [ ] PC/evidence gate exists and rejects missing, mismatched, unsafe, or success-claim packets.
- [ ] Robot diagnostics safe alias exists and only exposes whitelist summary fields.
- [ ] Mobile/web panel exists, fixture is valid JSON, and Start Delivery / Confirm Dropoff / Cancel remain disabled.
- [ ] Related `docs/interfaces/` and `docs/product/` docs are updated by implementation workers.
- [ ] Product closeout records no Objective 5 or Objective 1 percentage increase without real materials.
- [ ] Final closeout lists remaining real evidence gaps: real task record, Nav2/fixed-route runtime log, route completion signal, elevator evidence, dropoff/cancel completion, delivery result, true phone/browser evidence, public HTTPS/TLS, 4G/SIM, OSS/CDN, production DB/queue, worker/cutover, WAVE ROVER/UART/HIL, and PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.

## Planning-Pass Validation

The planning-only worker must run:

```bash
test -f sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/pre_start.md && test -f sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/prd.md && test -f sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_rerun_execution_result_acceptance_packet|software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet
git diff --check -- sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet
```
