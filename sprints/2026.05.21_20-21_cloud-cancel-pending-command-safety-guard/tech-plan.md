# Cloud Cancel Pending Command Safety Guard Tech Plan

Run time: 2026-05-21 20:05 CST

## Sprint Type

- sprint_type: epic
- capability: `cloud_cancel_pending_command_safety_guard`
- evidence_boundary: `software_proof_docker_cloud_cancel_pending_command_safety_guard`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。
2. 本 sprint 针对 Objective 5。
3. 选择理由：真实 O5 external materials 仍缺失，最近 18-19 与 19-20 final 均要求不要重复本地 wrapper；本轮选择一个独立、可 Docker 验证的 cloud command-safety 行为缺口，保持不涨百分比的证据边界。

## Recent PR / Review Evidence

- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；comment `3269642220` 只是 software-proof reply publication。
- PR #6 是 README/docs-only 合并，没有运行时、云、手机、硬件或交付证明。
- 最近 `cloud_manual_takeover_command_safety_guard`、`cloud_hosted_mobile_web_degradation_passthrough` 和 `cloud_support_handoff_safe_export` 已覆盖别的 O5 状态，本轮不能复用这些状态冒充新进展。

## Implementation Plan

### Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/operator_gateway_diagnostics.md`

Tasks:

1. Add canonical cancel-pending degraded-state helpers/constants.
2. Convert backend `cancel` response `state=busy` with pending-goal copy into the canonical degraded state before ACK/status propagation.
3. Add Robot/API diagnostics and phone readiness handling so command safety blocks primary actions and diagnostics remains available.
4. Add focused tests only around `cancel_pending_goal_acceptance`.
5. Update docs with the proof boundary and non-claims.

Acceptance commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "cloud_cancel_pending_command_safety_guard|cancel_pending_goal_acceptance|cancel_pending_not_delivery_success|software_proof_docker_cloud_cancel_pending_command_safety_guard" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/operator_gateway_diagnostics.md
```

### User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_cancel_pending_command_safety_guard.json`
- `docs/product/mobile_user_flow.md`

Tasks:

1. Render `cancel_pending_goal_acceptance` from safe Robot/API readiness fields.
2. Keep Start Delivery, Confirm Dropoff, and Cancel disabled; keep Diagnostics/Support Handoff visible.
3. Add one focused fixture and mobile-web test coverage for the new state.
4. Update mobile user-flow docs with non-claim wording.

Acceptance commands:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_cancel_pending_command_safety_guard.json >/dev/null
rg -n "cloud_cancel_pending_command_safety_guard|cancel_pending_goal_acceptance|cancel_pending_not_delivery_success|software_proof_docker_cloud_cancel_pending_command_safety_guard" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web docs/product/mobile_user_flow.md
```

### Hardware Infra Engineer

Allowed files: none.

Tasks:

1. Read `docs/vendor/VENDOR_INDEX.md` and relevant PR #5 boundary docs.
2. Confirm this sprint makes no hardware claim and does not resolve `PRRT_kwDOSWB9286CJ3tX`.

Acceptance commands:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "PRRT_kwDOSWB9286CJ3tX|3269642220|2D LiDAR|ToF|software_proof" OKR.md docs/product/production_hardware_boundary.md docs/vendor/VENDOR_INDEX.md
```

## Integration And Product Closeout

After worker evidence lands, Product updates:

- `sprints/2026.05.21_20-21_cloud-cancel-pending-command-safety-guard/tech-done.md`
- `sprints/2026.05.21_20-21_cloud-cancel-pending-command-safety-guard/side2side_check.md`
- `sprints/2026.05.21_20-21_cloud-cancel-pending-command-safety-guard/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Product acceptance commands:

```bash
test -f sprints/2026.05.21_20-21_cloud-cancel-pending-command-safety-guard/tech-done.md
test -f sprints/2026.05.21_20-21_cloud-cancel-pending-command-safety-guard/side2side_check.md
test -f sprints/2026.05.21_20-21_cloud-cancel-pending-command-safety-guard/final.md
rg -n "cloud_cancel_pending_command_safety_guard|software_proof_docker_cloud_cancel_pending_command_safety_guard|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven|PRRT_kwDOSWB9286CJ3tX|3269642220" sprints/2026.05.21_20-21_cloud-cancel-pending-command-safety-guard OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.21_20-21_cloud-cancel-pending-command-safety-guard OKR.md docs/process/okr_progress_log.md
```

## Boundary

This sprint must not claim real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser proof, WAVE ROVER/UART, HIL, route/elevator field pass, real cancel completion, delivery result, PR #5 resolution, or delivery success.
