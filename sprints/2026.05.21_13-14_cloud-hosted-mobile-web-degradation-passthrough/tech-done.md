# Cloud Hosted Mobile Web Degradation Passthrough Tech Done

## Sprint Declaration

- sprint_type: epic
- closeout_time: 2026-05-21 13:14 Asia/Shanghai
- capability: `cloud_hosted_mobile_web_degradation_passthrough`
- evidence_boundary: `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`
- accepted proof type: Docker/local software proof only

## User Value And Product North Star

本轮用户价值是让普通手机用户在 cloud-hosted same-origin mobile shell 里看到具体降级原因，而不是只看到泛化的 `status_present`。产品北极星仍是 phone-first trash delivery：手机是控制与恢复入口，但在任何降级状态下必须 fail closed，不能让用户误以为可以远程安全发车或已经交付成功。

## OKR Mapping

- Objective 5：主目标，cloud relay / phone control path 的 degraded state 可见性；保持约 68%，不因本轮 software proof 提升。
- Objective 4：次目标，手机端展示更清晰；保持约 99%，不等于 true phone/browser proof。
- Objective 1：守护目标，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending，comment `3269642220` 仅是 software-proof reply publication；保持约 81%。

## Actual Changes Recorded

Robot Platform Engineer changed:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/interfaces/ros_runtime_contracts.md`

Robot implementation evidence:

- `normalize_status()` preserves sanitized `remote_readiness` from relay status while forcing `source=software_proof`, `remote_ready=false`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Hosted `GET /api/status` passes through allow-listed `remote_readiness.degradation_state` values such as `command_pending` instead of flattening them to only generic `status_present`.
- Added `cloud_hosted_mobile_web_degradation_passthrough` and `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate` fields to the phone-safe status gate.
- Added focused regression coverage proving `status_present` with `remote_readiness.degradation_state=command_pending` returns `state=command_pending` while controls remain disabled.

Full-Stack Engineer changed:

- `mobile/web/app.js`
- `mobile/web/fixtures/cloud_hosted_mobile_web_degradation_passthrough.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Full-Stack implementation evidence:

- Mobile consumes hosted `/api/status` degraded states: `auth_failed`, `cloud_poll_backoff`, `manual_takeover_required`, `command_pending`, `command_expired`, `command_duplicate_deduped`, `command_id_conflict`, `command_sequence_regression`, `cloud_unreachable`, `malformed_response`.
- Mobile renders exact degraded states from `remote_readiness.degradation_state` with safe copy.
- Start Delivery / Confirm Dropoff / Cancel remain disabled for every degraded state.

## Validation Evidence From Engineers

Robot Platform Engineer reported:

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` passed.
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_static.py` passed: `Ran 87 tests ... OK`.
- Required `rg` passed.
- Scoped `git diff --check` passed.

Full-Stack Engineer reported:

- `node --check mobile/web/app.js` passed.
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` passed: `Ran 211 tests ... OK`.
- JSON fixture check passed.
- Required `rg` passed.
- Scoped `git diff --check` passed.

## Failures Fixed

- Robot first test run failed because a fixture omitted required `state`; fixed by adding the required state.
- Robot initial global `checksum` redaction broke backup/restore artifact tests; fixed by narrowing the redaction behavior and rerunning validation.
- Full-Stack first test run found fixture copy included `raw diagnostics`; fixed to safe Chinese wording and reran validation successfully.

## Acceptance Result

- P0 accepted: hosted `/api/status` now preserves safe specific `remote_readiness.degradation_state` for the hosted mobile shell.
- P0 accepted: all degraded states remain fail-closed with `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- P0 accepted: mobile renders state-specific safe copy while Start Delivery / Confirm Dropoff / Cancel remain disabled.
- P1 accepted: docs and sprint closeout preserve `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`.

## Evidence Boundary

This closeout accepts only `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`.

It is not real external cloud proof, not true phone/browser proof, not HIL, not WAVE ROVER/UART proof, not route/elevator field pass, not delivery result, not delivery success, and not PR #5 reviewer resolution.

## Remaining Risks

- Still missing real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, production worker/migration/cutover, production app/device, and true phone/browser evidence.
- Still missing real WAVE ROVER/UART/HIL, real 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry, and PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution.
- Still missing real Nav2/fixed-route runtime, route/elevator field pass, dropoff/cancel completion, delivery result, and delivery success.
