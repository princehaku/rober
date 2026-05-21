# Cloud ACK Accepted Result Pending Guard Tech Plan

Run time: 2026-05-22 00:01 Asia/Shanghai

## Sprint Type

- sprint_type: epic
- capability: `cloud_ack_accepted_result_pending_guard`
- degraded_state: `ack_accepted_result_pending`
- ack_semantics: `accepted_processing_only_not_delivery_success`
- evidence_boundary: `software_proof_docker_cloud_ack_accepted_result_pending_guard`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。Objective 1 约 81%，Objective 2 / 3 / 4 约 99%。
2. 本 sprint 针对 Objective 5。
3. 选择 Objective 5 的理由：用户要求优先推进完成度低的 OKR，且 O5 仍是最低；本机只有 Docker，没有真实外部云、4G、OSS/CDN、production DB/queue、真实手机/browser 或 delivery evidence，因此本轮只能做 software-proof 状态语义补强，不提高 O5 百分比。
4. 这不是重复前几轮 wrapper：`cloud_support_handoff_safe_export` 处理支持导出，`cloud_cancel_pending_command_safety_guard` 处理取消 pending，`cloud_ack_lookup_pending_status_guard` 处理 ACK missing / `ack_not_found`。本 sprint 专门处理 ACK 已 accepted/processing 但尚无真实 delivery result / dropoff completion / cancel completion 的中间态。

## Recent Evidence

- 最新 `sprints/2026.05.21_23-24_field-evidence-real-material-owner-ack-review-decision/final.md`：不要再做同一 owner-ack 层的本地 wrapper；下一步要么消费真实材料，要么升级缺失材料。
- 近期 O5 sprint 已做：`cloud_support_handoff_safe_export`、`cloud_cancel_pending_command_safety_guard`、`cloud_ack_lookup_pending_status_guard`。
- PR #5 live review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；comment `3269642220` 是 software-proof reply publication only。
- PR #6 是 README/docs-only，不提供 runtime、hardware 或 cloud proof。
- 本机无真实硬件，只有 Docker；不得声称真实 O5 external cloud、真实手机/browser、HIL、route/elevator field pass 或 delivery success。

## Product Contract

When command ACK is already accepted or processing but no terminal result exists, all user-facing and support-facing surfaces must expose the same canonical state:

- `capability=cloud_ack_accepted_result_pending_guard`
- `degradation_state=ack_accepted_result_pending`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `proof_boundary=software_proof_docker_cloud_ack_accepted_result_pending_guard`

This state means the control plane accepted or is processing the command. It does not mean the robot completed delivery, completed dropoff, completed cancel, reached a route/elevator field pass, or produced a terminal result.

## Implementation Plan

### Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/operator_gateway_diagnostics.md`

Tasks:

1. Add canonical accepted-result-pending readiness constants/helper:
   - `capability=cloud_ack_accepted_result_pending_guard`
   - `degradation_state=ack_accepted_result_pending`
   - `remote_ready=false`
   - `safe_to_control=false`
   - `delivery_success=false`
   - `primary_actions_enabled=false`
   - `retry_hint=wait_for_delivery_result_or_contact_support`
   - `ack_semantics=accepted_processing_only_not_delivery_success`
   - `proof_boundary=software_proof_docker_cloud_ack_accepted_result_pending_guard`
2. Apply the readiness helper when ACK status is accepted or processing but no terminal result / delivery result / dropoff completion / cancel completion is present.
3. Ensure diagnostics/phone readiness preserves the same state without raw tokens, Authorization headers, signed URLs, raw cloud responses, ROS topics, serial paths, tracebacks, WAVE ROVER details, or delivery-success wording.
4. Add focused tests for accepted/processing ACK without terminal result and diagnostics passthrough.
5. Update docs with the new endpoint/status behavior and proof boundary.
6. Keep all new technical code comments in Chinese and maintain the project comment-ratio requirement above 20%.

Acceptance commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "cloud_ack_accepted_result_pending_guard|ack_accepted_result_pending|accepted_processing_only_not_delivery_success|software_proof_docker_cloud_ack_accepted_result_pending_guard|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/operator_gateway_diagnostics.md
```

### User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_ack_accepted_result_pending_guard.json`
- `docs/product/mobile_user_flow.md`

Tasks:

1. Render `ack_accepted_result_pending` from safe Robot/API `remote_readiness`.
2. Copy must say the command has been accepted or is processing, but no real delivery/cancel/dropoff result exists yet.
3. Keep Start Delivery, Confirm Dropoff, and Cancel disabled; keep Diagnostics / Support Handoff visible.
4. Add one focused fixture and mobile-web test coverage.
5. Update mobile user-flow docs with non-claim wording.

Acceptance commands:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_ack_accepted_result_pending_guard.json >/dev/null
rg -n "cloud_ack_accepted_result_pending_guard|ack_accepted_result_pending|accepted_processing_only_not_delivery_success|software_proof_docker_cloud_ack_accepted_result_pending_guard|primary_actions_enabled=false|safe_to_control=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web docs/product/mobile_user_flow.md
```

### Product Manager / OKR Owner

Allowed files after implementation evidence lands:

- `sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/tech-done.md`
- `sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/side2side_check.md`
- `sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Tasks:

1. Verify Robot and Full-Stack evidence before closeout.
2. Preserve Objective 5 at about 68% unless real external cloud/phone/delivery evidence appears.
3. Record that this sprint is `software_proof_docker_cloud_ack_accepted_result_pending_guard`, not real external proof.
4. Preserve PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / material pending and comment `3269642220` as software-proof reply publication only.

Product acceptance commands:

```bash
test -f sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/tech-done.md
test -f sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/side2side_check.md
test -f sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard/final.md
rg -n "cloud_ack_accepted_result_pending_guard|software_proof_docker_cloud_ack_accepted_result_pending_guard|ack_accepted_result_pending|accepted_processing_only_not_delivery_success|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven|PRRT_kwDOSWB9286CJ3tX|3269642220" sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_00-01_cloud-ack-accepted-result-pending-guard OKR.md docs/process/okr_progress_log.md
```

### Hardware Infra Engineer

Allowed files: none.

Tasks:

1. Read-only consultation only if implementation wording risks hardware claims.
2. Confirm this sprint makes no WAVE ROVER, UART, serial, voltage, 2D LiDAR, ToF, HIL, route/elevator field pass, or real-material claim.
3. Confirm `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending unless live GitHub evidence says otherwise.

Acceptance commands:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "PRRT_kwDOSWB9286CJ3tX|3269642220|2D LiDAR|ToF|software_proof" OKR.md docs/product/production_hardware_boundary.md docs/vendor/VENDOR_INDEX.md
```

## Integration Boundary

Accepted/processing ACK without terminal result is a read/status-side pending state. It must not enqueue, replay, cancel, confirm dropoff, move an ACK cursor, mutate command terminal state, infer delivery result, or enable primary controls.

If a true terminal result exists later, that result must be represented by a separate evidence-backed terminal state. The ACK accepted-result-pending guard must yield to real terminal result evidence, but must never invent it.

## Boundary

This sprint must not claim real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser proof, WAVE ROVER/UART, HIL, route/elevator field pass, real ACK delivery, dropoff/cancel completion, delivery result, PR #5 resolution, or delivery success. Objective 5 stays about 68% unless real external evidence is supplied.
