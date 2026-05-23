# Verified Terminal Result Material Owner Response Review Handoff Tech Plan

Run time: 2026-05-23 22:02 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Goal

Build `verified_terminal_result_material_owner_response_review_handoff` as a safe owner/support/reviewer handoff packet derived from `verified_terminal_result_material_owner_response_review_decision`.

Required boundary:

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate`

This sprint must not claim real terminal result, O5 external proof, true phone/browser proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, route/elevator field pass, HIL, WAVE ROVER/UART proof, PR #5 resolved, or delivery success.

## OKR 最低优先级核对

1. Current `OKR.md` 4.1 lowest Objective: Objective 5, about 68%.
2. This sprint targets Objective 5 because the verified terminal-result material handoff is part of the phone/cloud terminal-result evidence chain.
3. It is not another `cloud_command_lifecycle_replay_*` wrapper. The latest O5 sprint already warned not to add more local O5 metadata depth without CEO direction. This sprint instead continues the existing material ladder from `verified_terminal_result_material_owner_response_review_decision` to `verified_terminal_result_material_owner_response_review_handoff`.
4. No OKR percentage lift is expected unless real external proof or verified terminal result materials arrive. Docker/local software proof stays `not_proven`.

## Evidence Sources

- `OKR.md` 4.1: Objective 5 about 68%, Objective 1 about 81%, Objective 2/3/4 about 99%.
- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/final.md`: closeout says not to add another local O5 metadata wrapper; real O5 external evidence or real material evidence is still missing.
- `sprints/2026.05.23_14-15_verified-terminal-result-material-owner-response-review-decision/final.md`: direct predecessor closed `verified_terminal_result_material_owner_response_review_decision`.
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX`: remains unresolved / `hardware_material_pending`.
- Product docs: `docs/product/mobile_user_flow.md` and `docs/product/remote_4g_mvp.md` already define fail-closed mobile/cloud terminal-result semantics.

## Parallel Worker Plan

### Task A: Full-Stack PC Gate

Owner: `full-stack-software-engineer`

Allowed file range:

- `pc-tools/evidence/`
- `pc-tools/tests/` or the existing PC evidence test layout
- `pc-tools/README.md`
- `docs/interfaces/verified_terminal_result_material_owner_response_review_handoff.md`

Work:

- Add a PC-only evidence gate for `verified_terminal_result_material_owner_response_review_handoff`.
- Derive the handoff only from safe `verified_terminal_result_material_owner_response_review_decision` metadata.
- Include focused tests for accepted handoff, missing/backfill handoff, evidence-ref mismatch, unsafe raw fields, and true-state flags.
- Update PC README and interface docs with schema, safe fields, fail-closed conditions, and proof boundary.

Acceptance commands:

```bash
python3 -m py_compile <touched pc-tools python files>
python3 -m unittest <focused PC evidence tests>
rg -n "verified_terminal_result_material_owner_response_review_handoff|software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" pc-tools docs/interfaces
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

- Add `robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary` as a read-only safe alias.
- Preserve upstream decision status, safe `evidence_ref`, safe `command_id`, owner/support/reviewer routing, next required evidence, safe copy, and required false-state fields.
- Fail closed on unsafe raw fields, credentials, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, success wording, or true control flags.
- Update interface and remote 4G product docs.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary|verified_terminal_result_material_owner_response_review_handoff|software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
```

### Task C: Full-Stack Mobile Read-only Panel

Owner: `full-stack-software-engineer`

Allowed file range:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Work:

- Add a read-only mobile/web panel for `verified_terminal_result_material_owner_response_review_handoff`.
- Consume `robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary` first, then compatible safe summary fields already available from `/api/status`, `phone_readiness`, `/api/diagnostics`, or nested diagnostics summaries.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled. Do not fetch raw materials, raw diagnostics, ACK/cursor routes, review routes, handoff routes, or any control path.
- Add fixture and focused mobile tests for visible handoff copy, false-state fields, and unsafe fail-closed behavior.
- Update `docs/product/mobile_user_flow.md`.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "verified_terminal_result_material_owner_response_review_handoff|software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Interface Contract

Expected summary names:

- `verified_terminal_result_material_owner_response_review_handoff`
- `verified_terminal_result_material_owner_response_review_handoff_summary`
- `robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary`

Expected safe fields:

- `schema`
- `schema_version`
- `capability=verified_terminal_result_material_owner_response_review_handoff`
- `source=software_proof`
- `safe_evidence_ref` or safe `evidence_ref`
- safe `command_id` when available
- source review decision status
- terminal result type
- owner/support/reviewer handoff route
- decision reasons
- missing/rejected materials
- next required evidence
- blocker reason
- safe copy text
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Forbidden fields or claims:

- real terminal result
- O5 external proof
- true phone/browser proof
- public HTTPS/TLS
- 4G/SIM
- OSS/CDN live traffic
- production DB/queue
- worker/cutover
- route/elevator field pass
- HIL
- WAVE ROVER/UART proof
- PR #5 resolved
- delivery success
- raw ROS topics, `/cmd_vel`, serial paths, baudrate, credentials, local paths, complete artifacts, checksums, tracebacks, ACK payloads, cursor mutation, command replay, or control authorization

## Product Closeout Plan

After workers finish, Product Manager / OKR Owner owns:

- `sprints/2026.05.23_22-23_verified-terminal-result-material-owner-response-review-handoff/tech-done.md`
- `sprints/2026.05.23_22-23_verified-terminal-result-material-owner-response-review-handoff/side2side_check.md`
- `sprints/2026.05.23_22-23_verified-terminal-result-material-owner-response-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Closeout must state whether Objective 5 remains about 68% and whether no OKR percentage lift still applies.

## Planning Verification

The planning-only acceptance commands for this Product run are:

```bash
test -f sprints/2026.05.23_22-23_verified-terminal-result-material-owner-response-review-handoff/pre_start.md && test -f sprints/2026.05.23_22-23_verified-terminal-result-material-owner-response-review-handoff/prd.md && test -f sprints/2026.05.23_22-23_verified-terminal-result-material-owner-response-review-handoff/tech-plan.md
rg -n "sprint_type: epic|verified_terminal_result_material_owner_response_review_handoff|software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate|Objective 5|OKR 最低优先级核对|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.23_22-23_verified-terminal-result-material-owner-response-review-handoff
git diff --check -- sprints/2026.05.23_22-23_verified-terminal-result-material-owner-response-review-handoff
```

