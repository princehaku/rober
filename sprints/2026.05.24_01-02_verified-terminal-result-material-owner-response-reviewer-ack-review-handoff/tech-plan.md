# Verified Terminal Result Material Owner Response Reviewer ACK Review Handoff Tech Plan

Run time: 2026-05-24 01:02 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Goal

Build `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff` as the next safe workflow rung after `verified_terminal_result_material_owner_response_reviewer_ack_review_decision`.

Required boundary:

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate`

This sprint must not claim PR #5 resolved, HIL, true phone/browser proof, real terminal result, real delivery/dropoff/cancel result, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, WAVE ROVER/UART proof, LiDAR/ToF installed proof, route/elevator field pass, or delivery success.

## OKR 最低优先级核对

1. Current `OKR.md` 4.1 lowest Objective: Objective 5, about 68%.
2. Other current Objective progress: Objective 1 about 81%; Objective 2/3/4 about 99%.
3. This sprint targets Objective 5 because reviewer ACK review handoff is part of the verified terminal-result material evidence workflow consumed by support, field owner, reviewer, Robot diagnostics, and mobile/web.
4. The sprint also touches Objective 1 and Objective 4 boundaries, but only to keep PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending` and mobile read-only / fail-closed.
5. No OKR percentage lift is expected unless real external O5 proof, verified terminal delivery/dropoff/cancel result, true phone/browser proof, or real PR #5 hardware materials arrive during or before closeout.

## Evidence Sources

- `OKR.md` 4.1: Objective 5 about 68%, Objective 1 about 81%, Objective 2/3/4 about 99%.
- `sprints/2026.05.24_00-01_verified-terminal-result-material-owner-response-reviewer-ack-review-decision/final.md`: direct predecessor closed `verified_terminal_result_material_owner_response_reviewer_ack_review_decision` as `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_gate`; no OKR percentage lift.
- PR #5 live review-thread evidence supplied for this planning run: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, and `PRRT_kwDOSWB9286CJ3tX` is_resolved=false / `hardware_material_pending`.
- Current host boundary: Docker/local only; no real hardware, public cloud, 4G/SIM, OSS/CDN, production DB/queue, true phone/browser, HIL, WAVE ROVER/UART, LiDAR/ToF, or route/elevator field materials are present.
- `docs/product/mobile_user_flow.md`: terminal-result material panels must be read-only, phone-safe, and not delivery success; Start Delivery / Confirm Dropoff / Cancel remain disabled.
- `docs/product/remote_4g_mvp.md`: Docker/local cloud/phone/ACK evidence cannot be presented as real public cloud, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, HIL, or delivery success.

## Parallel Owner Tasks

### Task A: Autonomy/PC Evidence Gate

Owner: `autonomy-engineer`

Allowed file range:

- `pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.py`
- focused PC evidence test for `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff` under the existing PC test layout
- `pc-tools/README.md`
- `docs/interfaces/verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.md`

Work:

- Add a PC-only evidence gate for `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`.
- Derive the handoff only from safe `verified_terminal_result_material_owner_response_reviewer_ack_review_decision` metadata.
- Classify safe handoff states: ready for real-material reviewer handoff, missing material, reassignment required, rejected unsafe, blocked missing source review-decision, and evidence-ref mismatch.
- Include focused tests for ready handoff, missing/backfill handoff, reassignment, missing source review-decision, evidence-ref mismatch, unsafe raw fields, unsafe success/control claims, PR #5 resolved wording rejection, and required false-state flags.
- Update PC README and interface docs with schema, safe fields, fail-closed conditions, and proof boundary.

Interface impact:

- New PC artifact and summary names are additive.
- No ROS topic, ACK/cursor mutation, GitHub mutation, material upload, robot command, delivery-state mutation, or control endpoint is allowed.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.py
python3 -m unittest pc-tools/evidence/test_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.py
rg -n "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" pc-tools docs/interfaces/verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.md
git diff --check -- pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.py pc-tools/evidence/test_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.py pc-tools/README.md docs/interfaces/verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.md
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

- Add `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary` as a read-only safe alias.
- Preserve safe source reviewer ACK review-decision status, handoff status, safe `evidence_ref`, safe `command_id`, owner/support/reviewer route, missing/rejected materials, reassignment reason, next required evidence, safe copy, and required false-state fields.
- Fail closed on unsafe raw fields, credentials, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, success wording, PR #5 resolved wording, HIL wording, or true control flags.
- Update interface and remote 4G product docs.

Interface impact:

- Robot diagnostics/status can expose only sanitized summary metadata.
- Existing command safety, ACK/cursor, cloud bridge, and task execution semantics must not change.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary|verified_terminal_result_material_owner_response_reviewer_ack_review_handoff|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
```

### Task C: Full-Stack Mobile Read-only Panel

Owner: `full-stack-software-engineer`

Allowed file range:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Work:

- Add a read-only `mobile/web` panel for `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`.
- Consume `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary` first, then compatible safe summary fields already available from `/api/status`, `phone_readiness`, `/api/diagnostics`, or nested diagnostics summaries.
- Show handoff status, source review-decision status, safe IDs, owner/support/reviewer route, missing/rejected classifications, next required evidence, PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`, evidence boundary, safe copy, and required false-state flags.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled. Do not fetch raw materials, raw diagnostics, ACK/cursor routes, review routes, handoff routes, owner-response routes, reviewer-ACK routes, material upload, GitHub mutation, replay/resubmit, or any control path.
- Add fixture and focused mobile tests for visible handoff copy, missing/reassignment/unsafe states, false-state fields, unsafe fail-closed behavior, and disabled primary actions.
- Update `docs/product/mobile_user_flow.md`.

Interface impact:

- Mobile panel is display-only and additive.
- Existing primary action gating remains controlled only by existing fail-closed gates.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D: Product Closeout

Owner: `product-okr-owner`

Allowed file range:

- `sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/tech-done.md`
- `sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/side2side_check.md`
- `sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Work:

- Record actual worker changes, validation outputs, acceptance decision, and evidence boundary.
- Update OKR/progress log conservatively after implementation evidence arrives.
- Keep Objective 5 about 68% unless implementation receives real external O5 proof, verified terminal delivery/dropoff/cancel result, true phone/browser proof, or production cloud proof.
- Keep Objective 1 about 81% unless PR #5 real hardware materials and reviewer resolution arrive.
- Keep Objective 2/3/4 at about 99% unless real route/elevator/Nav2/fixed-route/mobile-device evidence arrives.

Acceptance commands:

```bash
test -f sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/tech-done.md
test -f sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/side2side_check.md
test -f sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/final.md
rg -n "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" OKR.md docs/process/okr_progress_log.md sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff
```

## Interface Contract

Expected names:

- `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`
- `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary`
- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary`

Expected safe fields:

- `schema`
- `schema_version`
- `capability=verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`
- `source=software_proof`
- safe `evidence_ref` or `safe_evidence_ref`
- safe `command_id` when available
- source reviewer ACK review-decision status
- reviewer ACK review handoff status
- terminal result type
- owner/support/reviewer route
- missing or rejected materials
- reassignment reason when present
- handoff reasons
- next required evidence
- blocker reason when present
- safe copy text
- PR #5 thread status `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate`
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
- LiDAR/ToF installed proof
- route/elevator field pass
- delivery success
- raw ROS topics, `/cmd_vel`, serial paths, baudrate, credentials, local paths, complete artifacts, checksums, tracebacks, ACK payloads, cursor mutation, command replay, material upload, GitHub review mutation, or control authorization

## Evidence Boundary

This sprint can only produce `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate` on the current host.

It is explicitly:

- not real HIL
- not real WAVE ROVER/UART proof
- not real 2D LiDAR / ToF installed proof
- not true phone/browser proof
- not real public HTTPS/TLS
- not real 4G/SIM
- not OSS/CDN live traffic
- not production DB/queue
- not production worker/cutover
- not verified terminal delivery/dropoff/cancel result
- not route/elevator field pass
- not delivery success
- not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution

## Planning Verification

The planning-only acceptance commands for this Product run are:

```bash
test -f sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/pre_start.md
test -f sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/prd.md
test -f sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|verified_terminal_result_material_owner_response_reviewer_ack_review_handoff|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff
git diff --check -- sprints/2026.05.24_01-02_verified-terminal-result-material-owner-response-reviewer-ack-review-handoff
```
