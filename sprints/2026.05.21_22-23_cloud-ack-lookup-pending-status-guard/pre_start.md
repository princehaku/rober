# Cloud ACK Lookup Pending Status Guard Pre-Start

Run time: 2026-05-21 22:07 CST

## Sprint Type

- sprint_type: epic
- capability: `cloud_ack_lookup_pending_status_guard`
- degraded_state: `ack_lookup_pending`
- ack_semantics: `ack_lookup_pending_not_delivery_success`
- evidence_boundary: `software_proof_docker_cloud_ack_lookup_pending_status_guard`

## Evidence-First Rerank

`OKR.md` 4.1 shows Objective 5 as the lowest objective at about 68%. It remains blocked on real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser evidence, WAVE ROVER/HIL, and real delivery evidence. This sprint can only create Docker-only software proof and must not increase O5 percentage.

The latest closeout `sprints/2026.05.21_21-22_field-evidence-real-material-owner-ack-intake/final.md` explicitly says the next useful evidence is not another local metadata wrapper. If O5 is selected, it must be a distinct control-plane gap rather than another wrapper around the same missing external materials.

Recent PR #5 review evidence remains conservative:

- `PRRT_kwDOSWB9286CJ3tQ` is resolved.
- `PRRT_kwDOSWB9286CJ3tU` is resolved.
- `PRRT_kwDOSWB9286CJ3tX` is still unresolved / material pending.
- Comment `3269642220` is only software-proof reply publication and does not prove reviewer resolution, real 2D LiDAR / ToF materials, WAVE ROVER/UART/HIL, or delivery success.

## Product Contract Evidence

`docs/product/remote_4g_mvp.md` defines the phone-safe ACK read endpoint:

- `GET /robots/{robot_id}/commands/{command_id}/ack`
- A missing ACK returns `ack_not_found`.
- Phone UX should keep polling or show that the robot has not processed the command yet.
- ACK is command-processing evidence only; it is not dropoff completion, delivery result, or delivery success.

Current local code evidence in `operator_gateway_http.py`:

- `MockCloudStore.get_ack` returns `404` with plain `remote_error("ack_not_found", ...)` when an ACK is missing.
- That response does not include canonical phone-safe `remote_readiness`.
- The phone surface can therefore confuse missing ACK with a generic error unless the state is normalized into a fail-closed pending contract.

## Objective

Create an implementation-ready sprint plan for `cloud_ack_lookup_pending_status_guard`: when the phone queries a command ACK and it is missing, Robot/API and mobile/web must surface a named pending state that means "robot has not processed this command yet; keep waiting/support only." The contract must disable Start Delivery, Confirm Dropoff, and Cancel while preserving diagnostics/support.

## User Value

When a normal phone user checks a command ACK, missing ACK must not look like success, failure, or permission to submit more primary actions. It should say the robot has not processed the command yet, keep the operator in a waiting/support path, and preserve enough diagnostics for support to investigate without exposing raw cloud or ROS internals.

## Product North Star

普通用户只用手机也能理解远程控制状态：缺 ACK 是“机器人尚未处理 / 继续等待”，不是送达成功、不是失败完成、也不是可继续下发主操作。

## Owners

- Robot Platform Engineer: owns Robot/API ACK lookup normalization, diagnostics readiness, focused Python tests, and interface/product docs.
- User Touchpoint Full-Stack Engineer: owns mobile/web rendering, fixture, focused UI tests, and phone-flow docs.
- Hardware Infra Engineer: read-only PR #5/vendor boundary consultation; no hardware config changes.
- Product Manager / OKR Owner: owns this planning sprint and later closeout/OKR wording after worker evidence lands.

## Blocker Reuse Check

This sprint does not consume the missing public HTTPS/TLS, 4G/SIM, OSS/CDN, production DB/queue, production worker/cutover, true phone/browser, or hardware-material blocker as its main result. It targets a distinct local control-plane ACK-read gap that is testable in Docker-only software proof.

## Non-Claims

This sprint is not real cloud proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not production worker/cutover, not true phone/browser proof, not WAVE ROVER/UART/HIL, not route/elevator field pass, not dropoff/cancel completion, not delivery result, not delivery success, and not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.
