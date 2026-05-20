# Cloud Auth Failure Status Guard PRD

## User Value

普通手机用户遇到远程鉴权失败时，不应该看到 raw HTTP、token、Authorization、ROS topic 或底层调试细节，也不应该误以为命令已经送达成功。本轮把鉴权失败收敛成明确的手机可读状态：登录或访问凭证需要处理，主操作保持不可用，ACK 不代表送达成功。

## OKR Mapping

- Objective 5：云中转 + OSS/CDN 数据通路产品化，KR5 凭证管理 contract 与 KR6 graceful degradation。
- 本轮针对 Objective 5 的 command/status/ack 安全语义，不推进真实 external proof。
- Objective 1 / PR #5 真实硬件材料仍缺，本轮不处理 WAVE ROVER/UART/HIL 或 2D LiDAR / ToF material。

## Requirements

### P0 Robot / Operator Contract

When remote auth fails, the Robot/operator-safe status must expose:

- `degradation_state=auth_failed`
- `auth_state=auth_failed`
- `remote_ready=false`
- `primary_actions_enabled=false`
- `retry_hint=check_auth`
- `ack_semantics=auth_failed_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_auth_failure_status_guard`

The status must be redacted. It must not expose Authorization, bearer token, raw token, credential-bearing URL, traceback, local state path, `/cmd_vel`, serial, baudrate, WAVE ROVER, or raw ROS topic names.

### P0 Mobile Contract

`mobile/web` must display the auth failure as a read-only cloud readiness / command safety state. Start Delivery, Confirm Dropoff, and Cancel remain disabled. The phone copy must explain:

- 手机登录或访问码未通过。
- 需要重新登录或检查访问凭证。
- 这不是送达成功。

### P1 Documentation

Update product/interface-facing docs to record the new boundary and non-claims:

- `software_proof_docker_cloud_auth_failure_status_guard`
- not real HTTPS/TLS
- not 4G/SIM
- not OSS/CDN live traffic
- not production DB/queue
- not production worker/cutover
- not real phone/browser
- not WAVE ROVER/UART/HIL
- not delivery success
- not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved

## Acceptance

Robot focused tests prove auth failure produces the explicit boundary and redacted status. Mobile focused tests prove the fixture and UI text are present and actions remain disabled. Product closeout reruns the fenced commands and keeps OKR progress conservative.

## Non-Goals

This sprint does not add public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, real phone/browser acceptance, WAVE ROVER/UART/HIL, route/elevator field evidence, delivery result, or delivery success.
