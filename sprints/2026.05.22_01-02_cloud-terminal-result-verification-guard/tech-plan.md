# Cloud Terminal Result Verification Guard Implementation Plan

Run time: 2026-05-22 01:02 Asia/Shanghai

> For agentic workers: REQUIRED SUB-SKILL: use subagent-driven development or execute this plan task-by-task. Robot and Full-Stack tasks are independent by file scope and must be dispatched in parallel.

**Goal:** Prevent non-terminal result-like strings from being treated as verified delivery/dropoff/cancel terminal results.

**Architecture:** Robot/API owns canonical terminal-result verification and diagnostics status. Mobile/web consumes the safe `remote_readiness` state and renders it fail-closed without adding control behavior.

**Tech Stack:** Python ROS2 behavior package, dependency-free `mobile/web`, Python `unittest`, Node syntax check, JSON fixture validation, Markdown product/interface docs.

---

## Sprint Type

- sprint_type: epic
- capability: `cloud_terminal_result_verification_guard`
- degraded_state: `terminal_result_pending`
- related_previous_guard: `ack_accepted_result_pending`
- ack_semantics: `accepted_processing_only_not_delivery_success`
- evidence_boundary: `software_proof_docker_cloud_terminal_result_verification_guard`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。Objective 1 约 81%，Objective 2 / 3 / 4 约 99%。
2. 本 sprint 针对 Objective 5。
3. 选择 Objective 5 的理由：用户要求 O5 最低 OKR 下实际功能前进；上一轮 final 要求不要重复本地 metadata depth；本轮关闭的是一个 distinct backend verification gap：truthy result-like fields can bypass `ack_accepted_result_pending`.
4. 本 sprint 不提高 O5 百分比，因为当前没有真实外部云、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser、真实 delivery result 或 delivery success。

## Recent Evidence

- `OKR.md` 4.1：Objective 5 约 68%，仍最低。
- `sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/final.md`：上一轮 accepted/processing ACK without terminal result 已 fail-closed，并要求下一轮不要重复 O5 metadata depth。
- 主会话只读发现：`operator_gateway_http._has_terminal_delivery_result()` 对 `delivery_result` / `terminal_result` / `dropoff_completion` / `cancel_completion` 使用 truthy 判定，可能把 `"pending"`、`"accepted"`、`"processing"` 等非终态字符串当作 terminal result。
- PR #5 live review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；comment `3269642220` 不是 reviewer resolution。
- PR #6 无 review threads 且 docs-only。
- 本机只有 Docker；本轮 evidence boundary 必须是 `software_proof_docker_cloud_terminal_result_verification_guard`。

## Product Contract

Terminal-result checks must verify semantics, not mere presence.

Non-terminal values must not satisfy terminal delivery result checks:

- `pending`
- `accepted`
- `processing`
- `queued`
- `running`
- `in_progress`
- `submitted`
- `unknown`
- empty string / empty object / empty list

Verified terminal values may satisfy the check only when they are explicit terminal completion/failure/cancel states, or structured payloads with an explicit terminal field. Engineers should follow the existing local naming style and tests rather than inventing a large new state machine.

Canonical fail-closed state for non-terminal result-like fields:

- `capability=cloud_terminal_result_verification_guard`
- `degradation_state=terminal_result_pending`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `retry_hint=wait_for_verified_terminal_result_or_contact_support`
- `proof_boundary=software_proof_docker_cloud_terminal_result_verification_guard`

This state can coexist with or feed the previous `ack_accepted_result_pending` surface. The user-visible meaning stays the same: accepted/processing is not delivery success.

## File Structure

Robot Platform Engineer owns:

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- Modify as needed: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify tests: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- Modify tests as needed: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify docs: `docs/product/remote_4g_mvp.md`
- Modify docs as needed: `docs/interfaces/operator_gateway_diagnostics.md`

User Touchpoint Full-Stack Engineer owns:

- Modify: `mobile/web/app.js`
- Modify tests: `mobile/web/test_mobile_web_entrypoint.py`
- Create or modify fixture: `mobile/web/fixtures/robot_diagnostics_cloud_terminal_result_verification_guard.json`
- Modify docs: `docs/product/mobile_user_flow.md`

Product Manager / OKR Owner owns after implementation:

- Create/update: `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/tech-done.md`
- Create/update: `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/side2side_check.md`
- Create/update: `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

## Parallel Worker Plan

### Task A: Robot Platform Engineer - Backend Terminal Result Verification

**Files:**

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- Modify as needed: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify tests: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- Modify tests as needed: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify docs: `docs/product/remote_4g_mvp.md`
- Modify docs as needed: `docs/interfaces/operator_gateway_diagnostics.md`

**Steps:**

- [ ] Add focused failing tests for non-terminal strings in `delivery_result`, `terminal_result`, `dropoff_completion`, and `cancel_completion`.
- [ ] Run the focused tests and verify the current truthy check fails the new expectations.
- [ ] Replace truthy terminal-result detection with a small helper that rejects known non-terminal values and accepts only explicit terminal values or structured terminal payloads.
- [ ] Ensure the pending path emits or preserves `cloud_terminal_result_verification_guard`, `terminal_result_pending`, `ack_accepted_result_pending`, `accepted_processing_only_not_delivery_success`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- [ ] Update diagnostics normalization if it currently consumes the truthy result check.
- [ ] Update `docs/product/remote_4g_mvp.md` and, if touched, `docs/interfaces/operator_gateway_diagnostics.md`.
- [ ] Keep all new technical comments in Chinese and maintain the project comment-ratio requirement above 20%.

**Acceptance commands:**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "cloud_terminal_result_verification_guard|terminal_result_pending|ack_accepted_result_pending|accepted_processing_only_not_delivery_success|software_proof_docker_cloud_terminal_result_verification_guard|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/operator_gateway_diagnostics.md
```

### Task B: User Touchpoint Full-Stack Engineer - Mobile Fail-Closed Rendering

**Files:**

- Modify: `mobile/web/app.js`
- Modify tests: `mobile/web/test_mobile_web_entrypoint.py`
- Create or modify fixture: `mobile/web/fixtures/robot_diagnostics_cloud_terminal_result_verification_guard.json`
- Modify docs: `docs/product/mobile_user_flow.md`

**Steps:**

- [ ] Add a fixture where safe Robot/API status contains non-terminal result-like fields and `remote_readiness.capability=cloud_terminal_result_verification_guard`.
- [ ] Add focused tests proving the page renders the pending terminal-result copy and does not enable Start Delivery, Confirm Dropoff, or Cancel.
- [ ] Render `terminal_result_pending` as Chinese phone-safe copy: command/result field exists, but verified terminal delivery/dropoff/cancel result is still absent.
- [ ] Keep Diagnostics / Support Handoff visible while primary controls remain disabled.
- [ ] Update `docs/product/mobile_user_flow.md` with the new proof boundary and non-claim wording.

**Acceptance commands:**

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_terminal_result_verification_guard.json >/dev/null
rg -n "cloud_terminal_result_verification_guard|terminal_result_pending|ack_accepted_result_pending|accepted_processing_only_not_delivery_success|software_proof_docker_cloud_terminal_result_verification_guard|primary_actions_enabled=false|safe_to_control=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web docs/product/mobile_user_flow.md
```

### Task C: Product Manager / OKR Owner - Closeout After Evidence Lands

**Files:**

- Create/update: `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/tech-done.md`
- Create/update: `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/side2side_check.md`
- Create/update: `sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

**Steps:**

- [ ] Verify Robot and Full-Stack command outputs before closeout.
- [ ] Record actual changed files, validation outputs, deviations, and residual risk in `tech-done.md`.
- [ ] Record side-by-side acceptance: non-terminal result strings remain pending and fail-closed.
- [ ] Close `final.md` with Objective 5 held at about 68% unless real external evidence appears.
- [ ] Update `OKR.md` and `docs/process/okr_progress_log.md` conservatively; do not claim O5 numeric progress, PR #5 resolution, real cloud, real phone/browser, HIL, or delivery success.

**Acceptance commands:**

```bash
test -f sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/tech-done.md
test -f sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/side2side_check.md
test -f sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/final.md
rg -n "cloud_terminal_result_verification_guard|software_proof_docker_cloud_terminal_result_verification_guard|terminal_result_pending|ack_accepted_result_pending|accepted_processing_only_not_delivery_success|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven|PRRT_kwDOSWB9286CJ3tX|3269642220" sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard OKR.md docs/process/okr_progress_log.md
```

## Integration Boundary

This guard is read/status-side only. It must not enqueue, replay, cancel, confirm dropoff, advance ACK cursors, mutate command terminal state, infer delivery result, or enable primary controls.

The previous `ack_accepted_result_pending` guard remains valid. This sprint tightens the condition that decides whether a terminal result exists; it does not create a new success state.

## Hardware and External Proof Boundary

No hardware/vendor source is needed for implementation because this sprint does not touch WAVE ROVER, ESP32, Orange Pi UART, voltage, pinout, serial device, speed mapping, feedback protocol, mechanical dimensions, 2D LiDAR, ToF, Nav2, fixed-route, or elevator runtime. If any worker introduces hardware wording, they must re-check `docs/vendor/VENDOR_INDEX.md` and keep it as source-boundary only.

This sprint must not claim real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser proof, WAVE ROVER/UART, HIL, route/elevator field pass, real ACK delivery, dropoff/cancel completion, verified delivery result, PR #5 resolution, or delivery success.

## Main-Session Planning Validation

The planning-only Product Owner task must pass:

```bash
test -f sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/pre_start.md
test -f sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/prd.md
test -f sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|cloud_terminal_result_verification_guard|ack_accepted_result_pending|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_terminal_result_verification_guard" sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard
git diff --check -- sprints/2026.05.22_01-02_cloud-terminal-result-verification-guard
```
