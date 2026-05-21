# Cloud Hosted Mobile Web Degradation Passthrough Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or the repo-required Codex worker flow. Steps use checkbox (`- [ ]`) syntax for tracking. Main session must dispatch Engineer workers; main session must not directly edit product code, tests, hardware config, or runtime implementation.

**Goal:** Pass safe `remote_readiness.degradation_state` through the cloud-hosted same-origin mobile `/api/status` path so users see specific fail-closed degraded states instead of generic `status_present`.

**Architecture:** Robot/API remains the source of the sanitized hosted status response and proof boundary. `mobile/web` consumes the safe hosted payload and renders state-specific Chinese-first copy while keeping primary controls disabled. Product closeout records only Docker/local software proof and keeps OKR percentage language conservative.

**Tech Stack:** Python cloud relay / ROS2 behavior package, dependency-free `mobile/web`, Python `unittest`, Node syntax check, JSON fixture validation, scoped Markdown documentation.

---

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5, about 68%.
2. Next lowest Objective: Objective 1, about 81%, still blocked by PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`; reply comment id `3269642220` is not reviewer resolution.
3. This sprint targets Objective 5 because the cloud-hosted mobile web `/api/status` adapter belongs to the O5 cloud relay / phone control path.
4. This sprint must not claim percentage improvement because it is only `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`. There is still no real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, production app/device, or true phone/browser evidence.
5. This is not repeated blocker consumption because the latest final explicitly blocks another local wrapper around `field_evidence_rerun_execution_result_acceptance_backfill`; this sprint instead addresses a distinct hosted-shell degradation passthrough gap where upstream safe states exist but `/api/status` can flatten them to generic `status_present`.

## File Structure And Ownership

### Worker 1: Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `cloud-relay/README.md`
- `docs/interfaces/ros_runtime_contracts.md`

Responsibility:

- Preserve safe `remote_readiness.degradation_state` from latest relay status in cloud-hosted `GET /api/status`.
- Add or update the hosted status gate summary for `cloud_hosted_mobile_web_degradation_passthrough`.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and disabled command safety.
- Redact tokens, Authorization, raw cloud payloads, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, local paths, DB/queue URLs, tracebacks, checksums, and complete artifacts.

Validation commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
rg -n "cloud_hosted_mobile_web_degradation_passthrough|software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate|remote_readiness|degradation_state|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior cloud-relay/README.md docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior cloud-relay/README.md docs/interfaces/ros_runtime_contracts.md
```

### Worker 2: User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/cloud_hosted_mobile_web_degradation_passthrough.json`
- `docs/product/mobile_user_flow.md`

Responsibility:

- Add a representative hosted-status fixture for `cloud_hosted_mobile_web_degradation_passthrough`.
- Render exact degraded states from `remote_readiness.degradation_state` and safe copy.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled for every degraded state.
- Do not add replay, resubmit, ACK/cursor, raw diagnostics fetch, or any control endpoint.

Validation commands:

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/cloud_hosted_mobile_web_degradation_passthrough.json >/tmp/cloud_hosted_mobile_web_degradation_passthrough_fixture_check.json
rg -n "cloud_hosted_mobile_web_degradation_passthrough|software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate|auth_failed|cloud_poll_backoff|manual_takeover_required|command_pending|command_expired|command_duplicate_deduped|command_id_conflict|command_sequence_regression|cloud_unreachable|malformed_response|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web docs/product/mobile_user_flow.md
```

### Worker 3: Product Manager / OKR Owner

Allowed files after Engineer implementation:

- `sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/tech-done.md`
- `sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/side2side_check.md`
- `sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Responsibility:

- Verify Robot and Full-Stack evidence is present and scoped.
- Close only as `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`.
- Preserve Objective 5 about 68% unless real external materials appear.
- Preserve PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / material pending and comment id `3269642220` as software-proof reply publication only.

Validation commands:

```bash
test -f sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/tech-done.md
test -f sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/side2side_check.md
test -f sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/final.md
rg -n "cloud_hosted_mobile_web_degradation_passthrough|software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not real external cloud proof|not delivery success" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough
```

## Parallel Dispatch Plan

- Dispatch Worker 1 and Worker 2 in parallel because their write scopes are disjoint: Worker 1 owns relay/backend adapter and docs, Worker 2 owns mobile shell and product mobile doc.
- Worker 1 owns canonical hosted `/api/status` response fields. Worker 2 may start from a fixture contract but must align with Worker 1 before closeout if field names differ.
- Dispatch Worker 3 only after Worker 1 and Worker 2 return because Product closeout depends on actual Engineer evidence.
- If Worker 1 and Worker 2 disagree on field names, prefer the existing contract field `remote_readiness.degradation_state` and require fail-closed behavior before Product closeout.

## Required Guard Semantics

Hosted `/api/status`, Robot docs, and mobile fixture must converge on these fields or equivalent nested safe summary fields:

```text
capability=cloud_hosted_mobile_web_degradation_passthrough
proof_boundary=software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate
source=software_proof
not_proven
delivery_success=false
primary_actions_enabled=false
safe_to_control=false
remote_readiness.degradation_state=<safe state>
```

Required safe states:

```text
auth_failed
cloud_poll_backoff
manual_takeover_required
command_pending
command_expired
command_duplicate_deduped
command_id_conflict
command_sequence_regression
cloud_unreachable
malformed_response
```

The guard must fail closed if summary fields are missing, if an unsafe raw field appears, or if any path attempts to set `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true`.

## Acceptance Checklist

- [ ] Robot/API hosted `/api/status` preserves `remote_readiness.degradation_state` for degraded statuses.
- [ ] Robot/API tests show degraded states are not flattened into only `status_present`.
- [ ] Hosted status response includes `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`.
- [ ] Mobile fixture renders at least one specific degraded state and keeps Start Delivery / Confirm Dropoff / Cancel disabled.
- [ ] Mobile and backend outputs preserve `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- [ ] Docs state this is not real external cloud proof, not true phone/browser proof, not HIL, not WAVE ROVER/UART proof, not route/elevator field pass, and not delivery success.
- [ ] Sprint closeout states Objective 5 remains about 68% unless real external cloud/phone materials appear.

## Planning-Pass Validation

The planning-only worker must run:

```bash
test -f sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/pre_start.md && test -f sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/prd.md && test -f sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|cloud_hosted_mobile_web_degradation_passthrough|software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough
git diff --check -- sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough
```
