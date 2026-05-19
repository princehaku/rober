# Sprint 2026.05.20_02-03 Cloud Command Expiry Safety Guard - PRD

## 1. 用户价值

普通手机用户在弱网、排队或机器人长时间离线后，可能看到一条已经过期的云端指令。系统必须明确告诉用户“这条旧指令没有执行，请重新下发”，而不是静默忽略、继续显示可控制、或把 ACK/ignored 当成 delivery success。

## 2. OKR 映射

- Objective 5：云中转 + OSS/CDN 数据通路产品化。
  - KR1 command/status/ack 契约：过期 command 必须 ACK `ignored`，但不能进入本地 action。
  - KR6 graceful degradation：过期 command 是远程控制恢复路径的一类安全降级状态。
- Objective 4：手机用户体验与低成本量产边界。
  - 手机端必须用中文解释 `command_expired`，并保持主操作 fail-closed。

本轮不提高 Objective 5 百分比。O5 completion 仍需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 材料。本轮边界仅为 `software_proof_docker_cloud_command_expiry_safety_guard`。

## 3. 需求范围

### P0 Robot / Gateway

- 过期 remote command 不得调用 collect / confirm_dropoff / cancel 后端。
- 过期 command 必须 ACK `ignored`，message 包含 `expired` 或等价安全语义。
- operator status/readiness 必须暴露：
  - `degradation_state=command_expired`
  - `remote_ready=false`
  - `expired_command_id=<safe command id or [redacted]>`
  - `primary_actions_enabled=false`
  - `safe_phone_copy=上一条云端指令已过期，机器人没有执行，请重新下发。`
  - `retry_hint=resubmit_command`
  - `proof_boundary=software_proof_docker_cloud_command_expiry_safety_guard`
- `build_phone_readiness` 和 `command_safety` 必须识别 `command_expired`，并保持 Start / Confirm Dropoff / Cancel disabled；Diagnostics 保持可用。

### P0 Mobile

- mobile/web cloud readiness panel 消费 `command_expired`，展示中文 safe copy、`remote_ready=false`、`primary_actions_enabled=false`、ack semantics 和 proof boundary。
- 不新增任何 Start / Confirm Dropoff / Cancel endpoint，不缓存或重放控制请求。
- fixture 必须声明 `delivery_success=false`、`safe_to_control=false`、`not_proven`。

### P0 Product Closeout

- 更新 `OKR.md` 4.1 与 `docs/process/okr_progress_log.md`，保持 O5 约 68%，说明本轮只是 local/Docker software proof。
- sprint closeout 必须显式写明 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`。

## 4. 非目标

- 不证明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、多实例一致性、真实手机/browser、Nav2/fixed-route、WAVE ROVER/UART/HIL、dropoff/cancel completion 或 delivery success。
- 不关闭 PR #5 unresolved hardware material review thread。
- 不扩大 remote command schema beyond existing `expires_at` support。
