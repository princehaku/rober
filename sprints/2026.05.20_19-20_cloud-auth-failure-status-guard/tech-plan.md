# Cloud Auth Failure Status Guard Tech Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `2026.05.20_19-20_cloud-auth-failure-status-guard`
- Theme: `cloud_auth_failure_status_guard`
- Evidence boundary: `software_proof_docker_cloud_auth_failure_status_guard`
- Host: 本机没有真实硬件，只有 Docker。

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前完成度最低的是 Objective 5，约 68%。
2. 本 sprint 针对 Objective 5 的 command/status/ack credential failure graceful degradation。
3. 本 sprint 不直接推进真实 external proof，因为当前 Docker-only host 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser evidence。
4. Objective 1 约 81%，但 PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；本 sprint 不触碰 WAVE ROVER/UART/HIL 或真实 2D LiDAR / ToF materials。

## Architecture

Add an explicit auth failure proof boundary to the already existing remote degradation state:

```text
cloud auth failure
  -> Robot/operator safe status
  -> diagnostics and /api/status phone readiness
  -> mobile/web read-only cloud readiness and command safety copy
```

Required fields:

- `degradation_state=auth_failed`
- `auth_state=auth_failed`
- `remote_ready=false`
- `primary_actions_enabled=false`
- `retry_hint=check_auth`
- `ack_semantics=auth_failed_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_auth_failure_status_guard`

The path must fail closed. It must not create replay, resubmit, ACK, cursor, or control endpoints.

## Work Split

### Worker 1 - Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.20_19-20_cloud-auth-failure-status-guard/tech-done.md`

Tasks:

- Add `software_proof_docker_cloud_auth_failure_status_guard` constant where needed.
- Ensure auth failure status carries `ack_semantics=auth_failed_not_delivery_success` and `primary_actions_enabled=false`.
- Ensure operator HTTP and diagnostics propagate the same phone-safe state without exposing sensitive auth material.
- Add focused tests for bridge, HTTP status/readiness, and diagnostics-safe output.
- Update `docs/product/remote_4g_mvp.md`.

Validation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py

rg -n "cloud_auth_failure_status_guard|software_proof_docker_cloud_auth_failure_status_guard|auth_failed_not_delivery_success|auth_failed|check_auth|primary_actions_enabled=false" \
  onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md \
  sprints/2026.05.20_19-20_cloud-auth-failure-status-guard

git diff --check -- \
  onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md \
  sprints/2026.05.20_19-20_cloud-auth-failure-status-guard
```

### Worker 2 - User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_cloud_auth_failure_status_guard.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.20_19-20_cloud-auth-failure-status-guard/tech-done.md`

Tasks:

- Add a safe fixture for `cloud_auth_failure_status_guard`.
- Ensure mobile/web displays `auth_failed` as read-only cloud readiness / command safety copy.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not add replay, resubmit, ACK, cursor, diagnostics fetch, or control side effects.
- Update `docs/product/mobile_user_flow.md`.

Validation:

```bash
node --check mobile/web/app.js

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py

python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_auth_failure_status_guard.json >/dev/null

rg -n "cloud_auth_failure_status_guard|software_proof_docker_cloud_auth_failure_status_guard|auth_failed_not_delivery_success|auth_failed|check_auth|primary_actions_enabled=false|这不是送达成功" \
  mobile/web docs/product/mobile_user_flow.md \
  sprints/2026.05.20_19-20_cloud-auth-failure-status-guard

git diff --check -- \
  mobile/web docs/product/mobile_user_flow.md \
  sprints/2026.05.20_19-20_cloud-auth-failure-status-guard
```

### Product Closeout

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_19-20_cloud-auth-failure-status-guard/tech-done.md`
- `sprints/2026.05.20_19-20_cloud-auth-failure-status-guard/side2side_check.md`
- `sprints/2026.05.20_19-20_cloud-auth-failure-status-guard/final.md`

Tasks:

- Summarize actual worker output and validation.
- Keep Objective 5 around 68% unless real external proof appears.
- Keep Objective 1 around 81% and note PR #5 unresolved / material pending.
- Record explicit non-claims and next evidence requirements.

Validation:

```bash
test -f sprints/2026.05.20_19-20_cloud-auth-failure-status-guard/tech-done.md && \
test -f sprints/2026.05.20_19-20_cloud-auth-failure-status-guard/side2side_check.md && \
test -f sprints/2026.05.20_19-20_cloud-auth-failure-status-guard/final.md

rg -n "cloud_auth_failure_status_guard|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_auth_failure_status_guard|auth_failed_not_delivery_success|真实公网 HTTPS/TLS|4G/SIM|production DB/queue|delivery success" \
  OKR.md docs/process/okr_progress_log.md \
  sprints/2026.05.20_19-20_cloud-auth-failure-status-guard

git diff --check -- \
  OKR.md docs/process/okr_progress_log.md \
  sprints/2026.05.20_19-20_cloud-auth-failure-status-guard
```

## Non-Claims

This sprint is not real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, real phone/browser validation, WAVE ROVER/UART/HIL, route/elevator field pass, delivery result, delivery success, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.
