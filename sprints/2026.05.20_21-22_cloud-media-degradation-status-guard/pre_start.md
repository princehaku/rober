# Cloud Media Degradation Status Guard Pre Start

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.20_21-22_cloud-media-degradation-status-guard`
- Theme: `cloud_media_degradation_status_guard`
- Target boundary: `software_proof_docker_cloud_media_degradation_status_guard`
- Host context: 本机没有真实硬件，只有 Docker；本轮只做 OSS 写失败、CDN 不可达的 fail-closed degraded status 软件证明。
- Product north star: 用户在媒体上传或读取链路降级时，能明确知道远程媒体不可用、主操作被关闭、后续需要现场 owner 提供真实外部材料，而不是误以为任务已送达成功。

## Evidence Basis

`OKR.md` 4.1 显示当前完成度最低的是 Objective 5，约 68%。但 `OKR.md` 6 节也明确要求：Objective 5 只有拿到真实 external proof 时才应提高 completion，例如真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser 证据。

最新 sprint `sprints/2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision/final.md` 收口为 Objective 1 的 `software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate`，并明确 PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending。该证据不推进 Objective 5，也不证明真实硬件、HIL、真实手机/browser 或 delivery success。

最近 Objective 5 sprint `sprints/2026.05.20_19-20_cloud-auth-failure-status-guard/final.md` 已完成 `software_proof_docker_cloud_auth_failure_status_guard`，覆盖 auth failure fail-closed 状态。本轮不得重复 auth failure；本轮只覆盖 KR6 中 OSS 写失败、CDN 不可达两类媒体链路 degraded status。

自动化口径与记忆约束要求继续区分 software proof 与真实 external proof：本轮不能声称真实 OSS/CDN live traffic、真实公网 HTTPS/TLS、4G/SIM、production DB/queue、真实手机/browser、WAVE ROVER/UART/HIL、route/elevator field pass 或 delivery success。

## User Value

当垃圾投递任务相关媒体证据无法写入 OSS，或 CDN 无法读取时，用户和 operator 不应看到 raw exception、凭证、对象路径细节或模糊的 remote error；也不应误以为媒体已上传、任务已完成或可继续主操作。本轮把两类问题转成 Robot/API/mobile 可见的降级状态：

- OSS 写失败：提示媒体持久化失败，任务证据不可作为外部云证明。
- CDN 不可达：提示媒体读取不可用，不能把缓存、占位符或本地 fixture 当 live traffic。
- 两类状态都保持 `primary_actions_enabled=false`、`delivery_success=false`、`remote_ready=false`。

## OKR Mapping

- Objective 5：云中转 + OSS/CDN 数据通路产品化，KR6 graceful degradation。
- 本轮核心 KR：把 KR6 的 OSS 写失败、CDN 不可达从不可解释错误转成可见、可测试、可恢复的 degraded status。
- 本轮不推进 Objective 5 百分比完成度；除非后续收口拿到真实 external proof，否则 Objective 5 仍约 68%。
- Objective 1 / PR #5 仍保持材料待回填；本轮不处理 WAVE ROVER/UART/HIL、2D LiDAR / ToF 或 `PRRT_kwDOSWB9286CJ3tX` resolution。

## Core Lever

本轮抓手是“media degradation 状态产品化”，不是新增上传能力或 live probe：

1. Robot/API 侧必须生成统一 `cloud_media_degradation_status_guard` 状态。
2. Mobile 侧必须只读展示 OSS 写失败 / CDN 不可达，且主操作关闭。
3. 文档必须同步写清非声明边界和后续真实材料要求。

## Owners

- Robot Platform Engineer：Robot bridge / operator gateway / diagnostics 的媒体降级状态、API contract、focused Robot tests、`docs/product/remote_4g_mvp.md`。
- User Touchpoint Full-Stack Engineer：mobile/web fixture、只读 UI copy、focused mobile tests、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：本轮计划文档、后续 `tech-done.md` / `side2side_check.md` / `final.md` 收口、最终 `OKR.md` 与 `docs/process/okr_progress_log.md` 更新。

## Risks And Evidence Gaps

- 本轮只证明 Docker-only software proof，不证明真实 OSS 写入、真实 CDN fetch、真实公网 HTTPS/TLS、4G/SIM、production DB/queue、真实手机/browser 或 delivery success。
- 如果 worker 把媒体降级状态接成自动重试、ACK、cursor、命令重放或 Start/Confirm/Cancel enable，必须视为失败并回滚到 fail-closed contract。
- 如果输出包含 Authorization、bearer token、OSS AK/SK、对象签名 URL、traceback、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 或本地绝对路径，必须视为 redaction failure。
- 后续仍需要真实 external materials 才能提高 Objective 5 completion。

