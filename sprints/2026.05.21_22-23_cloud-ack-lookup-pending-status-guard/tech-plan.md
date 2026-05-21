# Cloud ACK Lookup Pending Status Guard Tech Plan

Run time: 2026-05-21 22:07 CST

## Sprint Type

- sprint_type: epic
- capability: `cloud_ack_lookup_pending_status_guard`
- degraded_state: `ack_lookup_pending`
- ack_semantics: `ack_lookup_pending_not_delivery_success`
- evidence_boundary: `software_proof_docker_cloud_ack_lookup_pending_status_guard`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。
2. 本 sprint 针对 Objective 5。
3. 选择理由：Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser 和真实交付证据，所以不能提高完成度；但 `GET /robots/{robot_id}/commands/{command_id}/ack` 的 missing ACK 仍缺 phone-safe pending readiness，这是不同于上一轮 metadata wrapper 的 distinct control-plane gap，可在 Docker-only 边界内推进。

## Recent Evidence

- 最新 `sprints/2026.05.21_21-22_field-evidence-real-material-owner-ack-intake/final.md`：下一步不是另一个本地 metadata wrapper；若继续 O5，必须是 distinct control-plane gap。
- PR #5 review evidence：`PRRT_kwDOSWB9286CJ3tQ`、`PRRT_kwDOSWB9286CJ3tU` 已 resolved；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；comment `3269642220` 只是 software-proof reply publication。
- `docs/product/remote_4g_mvp.md`：`GET /robots/{robot_id}/commands/{command_id}/ack` 的 missing ACK 返回 `ack_not_found`，手机应继续 polling 或显示 robot 尚未处理。
- `operator_gateway_http.py`：`MockCloudStore.get_ack` 当前 missing ACK 只返回 plain `remote_error("ack_not_found", ...)`，没有 canonical `remote_readiness`。

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

1. Add canonical ACK lookup pending readiness constants/helper:
   - `capability=cloud_ack_lookup_pending_status_guard`
   - `degradation_state=ack_lookup_pending`
   - `remote_ready=false`
   - `safe_to_control=false`
   - `delivery_success=false`
   - `primary_actions_enabled=false`
   - `retry_hint=continue_polling_or_contact_support`
   - `ack_semantics=ack_lookup_pending_not_delivery_success`
   - `proof_boundary=software_proof_docker_cloud_ack_lookup_pending_status_guard`
2. Make `MockCloudStore.get_ack` return `ack_not_found` plus canonical `remote_readiness` when the ACK is missing.
3. Ensure diagnostics/phone readiness preserves the same state without raw tokens, raw cloud response, ROS topics, serial paths, tracebacks, or delivery-success wording.
4. Add focused tests for missing ACK lookup and diagnostics passthrough.
5. Update docs with the new endpoint behavior and proof boundary.
6. Keep all new technical code comments in Chinese and maintain the project comment-ratio requirement above 20%.

Acceptance commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "cloud_ack_lookup_pending_status_guard|ack_lookup_pending|ack_lookup_pending_not_delivery_success|software_proof_docker_cloud_ack_lookup_pending_status_guard|ack_not_found" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md docs/interfaces/operator_gateway_diagnostics.md
```

### User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_ack_lookup_pending_status_guard.json`
- `docs/product/mobile_user_flow.md`

Tasks:

1. Render `ack_lookup_pending` from safe Robot/API `remote_readiness`.
2. Copy must say the robot has not processed the command yet and the user should keep waiting or contact support.
3. Keep Start Delivery, Confirm Dropoff, and Cancel disabled; keep Diagnostics / Support Handoff visible.
4. Add one focused fixture and mobile-web test coverage.
5. Update mobile user-flow docs with non-claim wording.

Acceptance commands:

```bash
node --check mobile/web/app.js
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_ack_lookup_pending_status_guard.json >/dev/null
rg -n "cloud_ack_lookup_pending_status_guard|ack_lookup_pending|ack_lookup_pending_not_delivery_success|software_proof_docker_cloud_ack_lookup_pending_status_guard" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web docs/product/mobile_user_flow.md
```

### Hardware Infra Engineer

Allowed files: none.

Tasks:

1. Read `docs/vendor/VENDOR_INDEX.md` and PR #5 boundary docs.
2. Confirm this sprint makes no WAVE ROVER, UART, serial, voltage, 2D LiDAR, ToF, HIL, or real-material claim.
3. Confirm `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending unless live GitHub evidence says otherwise.

Acceptance commands:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "PRRT_kwDOSWB9286CJ3tX|3269642220|2D LiDAR|ToF|software_proof" OKR.md docs/product/production_hardware_boundary.md docs/vendor/VENDOR_INDEX.md
```

## Integration And Product Closeout

After worker evidence lands, Product updates:

- `sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard/tech-done.md`
- `sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard/side2side_check.md`
- `sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Product acceptance commands:

```bash
test -f sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard/tech-done.md
test -f sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard/side2side_check.md
test -f sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard/final.md
rg -n "cloud_ack_lookup_pending_status_guard|software_proof_docker_cloud_ack_lookup_pending_status_guard|ack_lookup_pending|ack_lookup_pending_not_delivery_success|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven|PRRT_kwDOSWB9286CJ3tX|3269642220" sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.21_22-23_cloud-ack-lookup-pending-status-guard OKR.md docs/process/okr_progress_log.md
```

## Interface Boundary

Missing ACK lookup is a read-side pending state. It must not enqueue, replay, cancel, confirm dropoff, move an ACK cursor, mutate command state, or infer delivery result.

The response may preserve `404` / `ack_not_found`, but it must also provide safe `remote_readiness` so phone UI can render a controlled pending state.

## Boundary

This sprint must not claim real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser proof, WAVE ROVER/UART, HIL, route/elevator field pass, real ACK delivery, dropoff/cancel completion, delivery result, PR #5 resolution, or delivery success. Objective 5 stays about 68% unless real external evidence is supplied.
