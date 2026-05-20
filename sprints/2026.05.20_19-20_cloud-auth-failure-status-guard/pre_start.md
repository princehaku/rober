# Cloud Auth Failure Status Guard Pre Start

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.20_19-20_cloud-auth-failure-status-guard`
- Theme: `cloud_auth_failure_status_guard`
- Target boundary: `software_proof_docker_cloud_auth_failure_status_guard`
- Host context: 本机没有真实硬件，只有 Docker；本轮只做 command/status/ack 鉴权失败的软件证明。

## Evidence Basis

`OKR.md` 4.1 shows Objective 5 is still the lowest numerical objective at about 68%. It is blocked from real completion movement because this host has no public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser external evidence.

Recent sprint `sprints/2026.05.20_18-19_field-evidence-rerun-execution-pack/final.md` closed only `software_proof_docker_field_evidence_rerun_execution_pack_gate`. It explicitly did not prove O5 external cloud, real phone/browser, WAVE ROVER/UART/HIL, delivery result, or delivery success.

GitHub PR evidence remains unchanged: PR #5 thread `PRRT_kwDOSWB9286CJ3tX` is still unresolved / material pending after reply comment `3269642220`; PR #6 is README docs-only and has no runtime, hardware, HIL, phone/browser, or O5 external proof.

The recent O5 local control-plane chain already covered pending ACK, expired command, duplicate command idempotency, and command id conflict. The next Docker-actionable O5 gap is to make auth failure explicit, phone-safe, and fail-closed instead of leaving it as a generic remote degradation.

## Goal

When the cloud command/status/ack path fails authentication, Robot/operator/mobile must expose a safe and actionable state:

- `degradation_state=auth_failed`
- `auth_state=auth_failed`
- `remote_ready=false`
- `primary_actions_enabled=false`
- `retry_hint=check_auth`
- `ack_semantics=auth_failed_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_auth_failure_status_guard`

The safe copy must tell the user to log in again or check the access credential. It must not echo Authorization headers, bearer tokens, raw HTTP bodies, local paths, ROS topics, `/cmd_vel`, serial/UART data, or WAVE ROVER details.

## Owners

- Robot Platform Engineer: Robot bridge, operator HTTP readiness, diagnostics-safe auth failure status, focused Robot tests, and `docs/product/remote_4g_mvp.md`.
- User Touchpoint Full-Stack Engineer: mobile/web fixture, read-only UI copy, focused mobile test, and `docs/product/mobile_user_flow.md`.
- Product Manager / OKR Owner: final closeout, OKR/progress log, and sprint docs after workers return.

## Risks

- This must not be written as real cloud proof. It is Docker/local software proof only.
- This must not imply command ACK, delivery result, route/elevator completion, or hardware success.
- O5 percentage should stay conservative unless real external materials arrive.
