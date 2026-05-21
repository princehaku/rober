# Cloud Manual Takeover Command Safety Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or the repo-required Codex worker flow. Steps use checkbox (`- [ ]`) syntax for tracking. Main session must dispatch Engineer workers; main session must not directly edit product code, tests, hardware config, or runtime implementation.

**Goal:** Add a dedicated `cloud_manual_takeover_command_safety_guard` software-proof boundary so manual takeover / human-help states fail closed across Robot/API diagnostics and `mobile/web`.

**Architecture:** Robot/API becomes the source of the safe degraded state and diagnostics summary. `mobile/web` consumes only that safe state through existing `command_safety` and readiness inputs, rendering Chinese-first copy while keeping primary controls disabled. Product closeout preserves the Docker/local proof boundary and keeps OKR percentage language conservative.

**Tech Stack:** Python ROS2 behavior package, local/mock `operator_gateway_http`, `remote_bridge` readiness metadata, dependency-free `mobile/web`, Python `unittest`, Node syntax check, sprint/product Markdown docs.

---

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5, about 68%.
2. Next lowest Objective: Objective 1, about 81%, still blocked by PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / material pending.
3. This sprint targets Objective 5, the lowest Objective, but only as a bounded software-proof guard.
4. Reason for no percentage movement: current host has no real external cloud/phone materials. The sprint must not claim public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, true phone/browser proof, worker/cutover, HIL, WAVE ROVER, route/elevator field pass, or delivery success.
5. Reason this is not repeated blocker consumption: `docs/product/remote_4g_mvp.md` already names manual takeover as a command-safety blocker, while recent O5 guards cover stale status, pending ACK, auth failure, unreachable/malformed response, command ID conflict, command sequence regression, cloud poll backoff, media degradation, and manifest states. Manual takeover lacks its own dedicated `software_proof_docker_cloud_manual_takeover_command_safety_guard`.

## File Structure And Ownership

### Worker 1: Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_runtime_contracts.md`
- `docs/product/remote_4g_mvp.md`

Responsibility:

- Add and test the canonical Robot/API safe state for `manual_takeover_required`.
- Preserve `source=software_proof`, `not_proven`, `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Add `proof_boundary=software_proof_docker_cloud_manual_takeover_command_safety_guard`.
- Keep diagnostics visible but redacted.

Validation commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
rg -n "cloud_manual_takeover_command_safety_guard|manual_takeover_required|software_proof_docker_cloud_manual_takeover_command_safety_guard|delivery_success=false|primary_actions_enabled=false|remote_ready=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/ros_runtime_contracts.md
```

### Worker 2: User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_manual_takeover_command_safety_guard.json`
- `docs/product/mobile_user_flow.md`

Responsibility:

- Add or update a fixture for `robot_diagnostics_cloud_manual_takeover_command_safety_guard`.
- Render manual takeover / human-help state from safe Robot/API fields.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Avoid adding replay, resubmit, ACK/cursor, raw diagnostics fetch, or any control endpoint.

Validation commands:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_manual_takeover_command_safety_guard.json >/tmp/cloud_manual_takeover_fixture_check.json
rg -n "cloud_manual_takeover_command_safety_guard|manual_takeover_required|software_proof_docker_cloud_manual_takeover_command_safety_guard|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web docs/product/mobile_user_flow.md
```

### Worker 3: Product Manager / OKR Owner

Allowed files after Engineer implementation:

- `sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/tech-done.md`
- `sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/side2side_check.md`
- `sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Responsibility:

- Verify Robot and Full-Stack evidence is present.
- Close only as `software_proof_docker_cloud_manual_takeover_command_safety_guard`.
- Preserve Objective 5 about 68% and Objective 1 about 81% unless real materials appear.
- Explicitly preserve PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / material pending.

Validation commands:

```bash
test -f sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/tech-done.md
test -f sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/side2side_check.md
test -f sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/final.md
rg -n "cloud_manual_takeover_command_safety_guard|software_proof_docker_cloud_manual_takeover_command_safety_guard|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|manual_takeover_required|delivery_success=false|primary_actions_enabled=false|not real external cloud proof|not delivery success" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard
```

## Parallel Dispatch Plan

- Dispatch Worker 1 and Worker 2 in parallel because their write scopes are disjoint except product-contract wording; Worker 1 owns the canonical field semantics in Robot/API, Worker 2 consumes the safe summary and fixture.
- Dispatch Worker 3 only after Worker 1 and Worker 2 return, because Product closeout depends on actual Engineer evidence.
- If Worker 1 changes field names away from `manual_takeover_required`, Worker 2 must adjust fixture consumption before Product closeout. The preferred canonical field remains `degradation_state=manual_takeover_required`.

## Required Guard Semantics

Robot/API and mobile must converge on these fields or equivalent nested safe summary fields:

```text
capability=cloud_manual_takeover_command_safety_guard
degradation_state=manual_takeover_required
manual_takeover_required=true
remote_ready=false
safe_to_control=false
delivery_success=false
primary_actions_enabled=false
retry_hint=contact_support
ack_semantics=manual_takeover_not_delivery_success
proof_boundary=software_proof_docker_cloud_manual_takeover_command_safety_guard
```

Safe phone copy:

```text
需要人工接管；远程主操作已暂停，请按现场/支持指引处理。这不是送达成功。
```

The guard must fail closed if summary fields are missing, if an unsafe field is present, or if any path attempts to set `delivery_success=true` or `primary_actions_enabled=true`.

## Acceptance Checklist

- [ ] Robot/API exposes `manual_takeover_required` with the exact proof boundary.
- [ ] Robot/API tests show no local action execution, ACK success wording, cursor advance, or delivery success is created from manual takeover.
- [ ] Diagnostics summary is visible and redacted.
- [ ] Mobile fixture renders the state and keeps Start Delivery / Confirm Dropoff / Cancel disabled.
- [ ] Product docs state the proof is not real external cloud proof, true phone/browser proof, HIL, WAVE ROVER/UART proof, route/elevator field pass, or delivery success.
- [ ] Sprint closeout states Objective 5 and Objective 1 percentages do not increase unless real materials appear.

## Planning-Pass Validation

The planning-only worker must run:

```bash
test -f sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/pre_start.md
test -f sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/prd.md
test -f sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard/tech-plan.md
rg -n "sprint_type: epic|cloud_manual_takeover_command_safety_guard|software_proof_docker_cloud_manual_takeover_command_safety_guard|OKR 最低优先级核对|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|manual_takeover_required|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard
git diff --check -- sprints/2026.05.21_10-11_cloud-manual-takeover-command-safety-guard
```

