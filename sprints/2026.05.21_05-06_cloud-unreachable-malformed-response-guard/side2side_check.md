# Cloud Unreachable Malformed Response Guard Side2Side Check

## Acceptance Snapshot

- sprint_type: epic
- Evidence boundary: `software_proof_docker_cloud_unreachable_malformed_response_guard`
- Target states: `source=software_proof`, `not_proven`, `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`

## User Value And North Star

North star: ordinary phone users should understand when the robot cannot safely accept a remote command, without seeing ROS2, cloud logs, raw JSON, or hardware details.

This sprint improves that path for two failure modes:

- `cloud_unreachable`: cloud cannot be reached, so the phone must not offer primary operations.
- `malformed_response`: cloud returned an unsafe or unusable response, so the system must not guess success or ACK semantics.

## Side By Side Result

| Requirement | Result |
| --- | --- |
| Robot/API normalizes cloud unreachable and malformed cloud response | Met by `robot_diagnostics_cloud_unreachable_malformed_response_guard_summary`. |
| Preserve fail-closed flags | Met: `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `not_proven`. |
| Phone user sees Chinese, safe copy | Met by mobile/web rendering for `cloud_unreachable` and `malformed_response`. |
| Start / Confirm / Cancel disabled | Met per Full-Stack worker result. |
| Diagnostics / support remain visible | Met per Full-Stack worker result. |
| Docs synchronized | Met by Robot docs update in `docs/interfaces/ros_runtime_contracts.md` and Full-Stack docs updates in `docs/product/mobile_user_flow.md`, `docs/product/remote_4g_mvp.md`. |
| Objective 5 percentage movement | Not moved; remains about 68%. |

## Non-Claims Checked

This is not real external cloud proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not true phone/browser proof, not route/elevator field pass, not Nav2/fixed-route, not WAVE ROVER/UART/HIL, not dropoff/cancel completion, not delivery result, not delivery success, and not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.

## Product Acceptance

Accepted as a Docker/local O5 fail-closed guard sprint. It improves user-safe degraded-state visibility but does not increase OKR completion percentage because no real external cloud or phone/browser material was produced.
