# Cloud Media Degradation Status Guard Tech Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `2026.05.20_21-22_cloud-media-degradation-status-guard`
- Theme: `cloud_media_degradation_status_guard`
- Evidence boundary: `software_proof_docker_cloud_media_degradation_status_guard`
- Host: 本机没有真实硬件，只有 Docker。

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前完成度最低的是 Objective 5，约 68%。
2. 本 sprint 针对 Objective 5 KR6 的 OSS 写失败、CDN 不可达 graceful degradation。
3. 本 sprint 不直接推进真实 external proof，因为当前 Docker-only host 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser evidence。
4. 最近 O5 sprint `cloud_auth_failure_status_guard` 已覆盖 auth failure；本 sprint 明确不重复 auth failure，而是补 KR6 的 media degraded status。
5. Objective 1 约 81%，但 PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；本 sprint 不触碰 WAVE ROVER/UART/HIL 或真实 2D LiDAR / ToF materials。

## Architecture

在现有 remote readiness / diagnostics / mobile cloud-readiness 链路上增加一个只读媒体降级状态：

```text
OSS 写失败 / CDN 不可达
  -> Robot/API media degraded status
  -> operator diagnostics and phone readiness
  -> mobile/web read-only degraded media panel
```

Required shared fields:

- `degradation_state=media_degraded`
- `media_state=oss_write_failed` 或 `media_state=cdn_unavailable`
- `remote_ready=false`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `proof_boundary=software_proof_docker_cloud_media_degradation_status_guard`

OSS 写失败附加 fields:

- `retry_hint=check_oss_write`
- `ack_semantics=media_not_persisted_not_delivery_success`

CDN 不可达附加 fields:

- `retry_hint=check_cdn_reachability`
- `ack_semantics=media_not_fetchable_not_delivery_success`

The path must fail closed. It must not create replay, resubmit, ACK success, cursor movement, diagnostics fetch side effect, ROS command, hardware interaction, or control endpoint.

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
- `sprints/2026.05.20_21-22_cloud-media-degradation-status-guard/tech-done.md`

Tasks:

- Add or normalize `software_proof_docker_cloud_media_degradation_status_guard` where Robot/API readiness emits media degradation.
- Ensure OSS write failure emits `media_state=oss_write_failed`, `retry_hint=check_oss_write`, `ack_semantics=media_not_persisted_not_delivery_success`, `remote_ready=false`, `primary_actions_enabled=false`, and `delivery_success=false`.
- Ensure CDN unavailable emits `media_state=cdn_unavailable`, `retry_hint=check_cdn_reachability`, `ack_semantics=media_not_fetchable_not_delivery_success`, `remote_ready=false`, `primary_actions_enabled=false`, and `delivery_success=false`.
- Ensure diagnostics and operator HTTP readiness redact Authorization, bearer token, OSS AK/SK, signed URL, bucket secret, traceback, local absolute path, ROS topic, `/cmd_vel`, serial/UART, and WAVE ROVER details.
- Add focused Robot tests for bridge, HTTP status/readiness, and diagnostics-safe media degradation output.
- Update `docs/product/remote_4g_mvp.md` with the software-proof boundary, non-claims, and recovery expectations.
- Append Worker 1 actual changes, validation, failures, and risks to sprint `tech-done.md`.

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

rg -n "cloud_media_degradation_status_guard|software_proof_docker_cloud_media_degradation_status_guard|oss_write_failed|cdn_unavailable|media_not_persisted_not_delivery_success|media_not_fetchable_not_delivery_success|primary_actions_enabled=false|delivery_success=false" \
  onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md \
  sprints/2026.05.20_21-22_cloud-media-degradation-status-guard

git diff --check -- \
  onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md \
  sprints/2026.05.20_21-22_cloud-media-degradation-status-guard
```

### Worker 2 - User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_cloud_media_degradation_status_guard.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.20_21-22_cloud-media-degradation-status-guard/tech-done.md`

Tasks:

- Add a phone-safe fixture for `cloud_media_degradation_status_guard` that includes both `oss_write_failed` and `cdn_unavailable` examples.
- Ensure mobile/web displays OSS 写失败 as a read-only media degradation state with disabled primary actions and copy that says this is not delivery success.
- Ensure mobile/web displays CDN 不可达 as a read-only media degradation state with disabled primary actions and copy that says this is not delivery success.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not add replay, resubmit, ACK success, cursor movement, diagnostics fetch, or robot control side effects.
- Update `docs/product/mobile_user_flow.md` with the software-proof boundary, UX copy, and non-claims.
- Append Worker 2 actual changes, validation, failures, and risks to sprint `tech-done.md`.

Validation:

```bash
node --check mobile/web/app.js

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py

python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_media_degradation_status_guard.json >/dev/null

rg -n "cloud_media_degradation_status_guard|software_proof_docker_cloud_media_degradation_status_guard|oss_write_failed|cdn_unavailable|media_not_persisted_not_delivery_success|media_not_fetchable_not_delivery_success|primary_actions_enabled=false|delivery_success=false|这不是送达成功|OSS 写失败|CDN 不可达" \
  mobile/web docs/product/mobile_user_flow.md \
  sprints/2026.05.20_21-22_cloud-media-degradation-status-guard

git diff --check -- \
  mobile/web docs/product/mobile_user_flow.md \
  sprints/2026.05.20_21-22_cloud-media-degradation-status-guard
```

### Product Closeout

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.20_21-22_cloud-media-degradation-status-guard/tech-done.md`
- `sprints/2026.05.20_21-22_cloud-media-degradation-status-guard/side2side_check.md`
- `sprints/2026.05.20_21-22_cloud-media-degradation-status-guard/final.md`

Tasks:

- Summarize actual worker output and validation.
- Keep Objective 5 around 68% unless real external proof appears.
- Keep Objective 1 around 81% and note PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / material pending.
- Confirm this sprint did not repeat auth failure and did not claim OSS/CDN live traffic.
- Record explicit non-claims and next evidence requirements.

Validation:

```bash
test -f sprints/2026.05.20_21-22_cloud-media-degradation-status-guard/tech-done.md && \
test -f sprints/2026.05.20_21-22_cloud-media-degradation-status-guard/side2side_check.md && \
test -f sprints/2026.05.20_21-22_cloud-media-degradation-status-guard/final.md

rg -n "cloud_media_degradation_status_guard|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_cloud_media_degradation_status_guard|OSS 写失败|CDN 不可达|真实公网 HTTPS/TLS|4G/SIM|production DB/queue|delivery_success=false|delivery success" \
  OKR.md docs/process/okr_progress_log.md \
  sprints/2026.05.20_21-22_cloud-media-degradation-status-guard

git diff --check -- \
  OKR.md docs/process/okr_progress_log.md \
  sprints/2026.05.20_21-22_cloud-media-degradation-status-guard
```

## Parallel Launch Guidance

This is a 2-owner epic sprint. Robot Platform Engineer and User Touchpoint Full-Stack Engineer should be launched in parallel because their write scopes are disjoint except for appending to `tech-done.md`. To avoid append conflicts, each worker must append only under their own heading and must not rewrite the other worker's section.

The Product Manager / OKR Owner waits for both workers, then performs closeout only after validation evidence is returned.

## Non-Claims

This sprint is not real OSS write, real CDN fetch, OSS/CDN live traffic, real public HTTPS/TLS, 4G/SIM, production DB/queue, production worker/cutover, real phone/browser validation, WAVE ROVER/UART/HIL, route/elevator field pass, delivery result, delivery success, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.

