# Verified Terminal Result Material Owner Response Reviewer ACK Intake Tech Plan

Run time: 2026-05-23 23:04 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Goal

Build `verified_terminal_result_material_owner_response_reviewer_ack_intake` as the next safe workflow rung after `verified_terminal_result_material_owner_response_review_handoff`.

Required boundary:

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate`

This sprint must not claim PR #5 resolved, HIL, true phone/browser proof, real terminal result, real delivery/dropoff/cancel result, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, WAVE ROVER/UART proof, route/elevator field pass, or delivery success.

## OKR 最低优先级核对

1. Current `OKR.md` 4.1 lowest Objective: Objective 5, about 68%.
2. This sprint targets Objective 5 because reviewer ACK intake is part of the verified terminal-result material evidence workflow consumed by support, field owner, reviewer, Robot diagnostics, and mobile/web.
3. The sprint also touches Objective 4 and Objective 1 boundaries, but only to keep mobile read-only and preserve PR #5 unresolved / hardware-material-pending status.
4. No OKR percentage lift is expected unless real external O5 proof, verified terminal delivery/dropoff/cancel result, true phone/browser proof, or real PR #5 hardware materials arrive.

## Evidence Sources

- `OKR.md` 4.1: Objective 5 about 68%, Objective 1 about 81%, Objective 2/3/4 about 99%.
- `sprints/2026.05.23_22-23_verified-terminal-result-material-owner-response-review-handoff/final.md`: direct predecessor closed `verified_terminal_result_material_owner_response_review_handoff` as Docker/local software proof with no OKR percentage lift.
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX`: still unresolved / `hardware_material_pending`.
- `docs/product/mobile_user_flow.md`: terminal-result and handoff panels must be read-only, phone-safe, and not delivery success.
- `docs/product/remote_4g_mvp.md`: local/relay proof must preserve command/status/ACK semantics and avoid control authorization from support metadata.

## Parallel Worker Plan

### Task A: Full-Stack PC Gate

Owner: `full-stack-software-engineer`

Allowed file range:

- `pc-tools/evidence/`
- focused PC evidence tests under the existing PC test layout
- `pc-tools/README.md`
- `docs/interfaces/verified_terminal_result_material_owner_response_reviewer_ack_intake.md`

Work:

- Add a PC-only evidence gate for `verified_terminal_result_material_owner_response_reviewer_ack_intake`.
- Derive the intake only from safe `verified_terminal_result_material_owner_response_review_handoff` metadata.
- Classify reviewer ACK states: acknowledged, missing material, reassignment needed, rejected unsafe ACK, and blocked missing source handoff.
- Include focused tests for accepted ACK, missing/backfill ACK, reassignment, evidence-ref mismatch, unsafe raw fields, missing source handoff, and true-state flags.
- Update PC README and interface docs with schema, safe fields, fail-closed conditions, and proof boundary.

Acceptance commands:

```bash
python3 -m py_compile <touched pc-tools python files>
python3 -m unittest <focused PC evidence tests>
rg -n "verified_terminal_result_material_owner_response_reviewer_ack_intake|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" pc-tools docs/interfaces
git diff --check -- <Task A touched files>
```

### Task B: Robot Diagnostics Safe Alias

Owner: `robot-software-engineer`

Allowed file range:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py` only if the existing status/diagnostics export requires registration
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`

Work:

- Add `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary` as a read-only safe alias.
- Preserve source handoff status, safe `evidence_ref`, safe `command_id`, reviewer ACK status, owner/support/reviewer routing, next required evidence, safe copy, and required false-state fields.
- Fail closed on unsafe raw fields, credentials, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, success wording, PR #5 resolved wording, or true control flags.
- Update interface and remote 4G product docs.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary|verified_terminal_result_material_owner_response_reviewer_ack_intake|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
```

### Task C: Full-Stack Mobile Read-only Panel

Owner: `full-stack-software-engineer`

Allowed file range:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Work:

- Add a read-only `mobile/web` panel for `verified_terminal_result_material_owner_response_reviewer_ack_intake`.
- Consume `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary` first, then compatible safe summary fields already available from `/api/status`, `phone_readiness`, `/api/diagnostics`, or nested diagnostics summaries.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled. Do not fetch raw materials, raw diagnostics, ACK/cursor routes, review routes, handoff routes, owner-response routes, reviewer-ACK routes, or any control path.
- Add fixture and focused mobile tests for visible reviewer ACK copy, missing/reassignment/unsafe states, false-state fields, and unsafe fail-closed behavior.
- Update `docs/product/mobile_user_flow.md`.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "verified_terminal_result_material_owner_response_reviewer_ack_intake|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Interface Contract

Expected summary names:

- `verified_terminal_result_material_owner_response_reviewer_ack_intake`
- `verified_terminal_result_material_owner_response_reviewer_ack_intake_summary`
- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary`

Expected safe fields:

- `schema`
- `schema_version`
- `capability=verified_terminal_result_material_owner_response_reviewer_ack_intake`
- `source=software_proof`
- safe `evidence_ref` or `safe_evidence_ref`
- safe `command_id` when available
- source handoff status
- terminal result type
- reviewer ACK status
- owner/support/reviewer route
- missing or rejected materials
- reassignment reason when present
- next required evidence
- blocker reason when present
- safe copy text
- PR #5 thread status `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Forbidden fields or claims:

- PR #5 resolved
- HIL
- true phone/browser proof
- real terminal result
- verified delivery/dropoff/cancel result
- public HTTPS/TLS
- 4G/SIM
- OSS/CDN live traffic
- production DB/queue
- WAVE ROVER/UART proof
- route/elevator field pass
- delivery success
- raw ROS topics, `/cmd_vel`, serial paths, baudrate, credentials, local paths, complete artifacts, checksums, tracebacks, ACK payloads, cursor mutation, command replay, material upload, GitHub review mutation, or control authorization

## Product Closeout Plan

After workers finish, Product Manager / OKR Owner owns:

- `sprints/2026.05.23_23-24_verified-terminal-result-material-owner-response-reviewer-ack-intake/tech-done.md`
- `sprints/2026.05.23_23-24_verified-terminal-result-material-owner-response-reviewer-ack-intake/side2side_check.md`
- `sprints/2026.05.23_23-24_verified-terminal-result-material-owner-response-reviewer-ack-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Closeout must state whether Objective 5 remains about 68%, whether PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`, and whether no OKR percentage lift still applies.

## Planning Verification

The planning-only acceptance commands for this Product run are:

```bash
test -f sprints/2026.05.23_23-24_verified-terminal-result-material-owner-response-reviewer-ack-intake/pre_start.md && test -f sprints/2026.05.23_23-24_verified-terminal-result-material-owner-response-reviewer-ack-intake/prd.md && test -f sprints/2026.05.23_23-24_verified-terminal-result-material-owner-response-reviewer-ack-intake/tech-plan.md
rg -n "sprint_type: epic|verified_terminal_result_material_owner_response_reviewer_ack_intake|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate|Objective 5|OKR 最低优先级核对|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.23_23-24_verified-terminal-result-material-owner-response-reviewer-ack-intake
git diff --check -- sprints/2026.05.23_23-24_verified-terminal-result-material-owner-response-reviewer-ack-intake
```
