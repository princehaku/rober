# Cloud Media Degradation Status Guard PRD

## User Value And North Star

用户价值：当媒体证据链遇到 OSS 写失败或 CDN 不可达时，手机用户、operator 和 Robot diagnostics 都能看到一致的降级状态，知道“媒体链路不可用、主操作关闭、这不是送达成功”，而不是看到技术异常或误判任务已完成。

产品北极星：Objective 5 的云中转与媒体数据通路必须可解释、可恢复、可审计；即使真实外部云材料还不可用，本地 Docker-only proof 也要先把失败状态产品化，并保持 fail-closed。

## OKR Mapping

- Objective 5：云中转 + OSS/CDN 数据通路产品化，当前约 68%，是 `OKR.md` 4.1 当前最低 Objective。
- KR6：4G 中断、OSS 写失败、CDN 不可达三类失败必须 graceful degradation；本轮覆盖 OSS 写失败与 CDN 不可达。
- 本轮不覆盖 auth failure；`cloud_auth_failure_status_guard` 已在上一轮完成。
- 本轮不推进真实 external proof，不更新 `OKR.md` 百分比；最终收口时 Product 再基于 worker 证据决定是否只记录软件证明。

## KR Breakdown

### KR6-A OSS 写失败 degraded status

当媒体写入 OSS 失败时，Robot/API/mobile 必须暴露：

- `degradation_state=media_degraded`
- `media_state=oss_write_failed`
- `remote_ready=false`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `retry_hint=check_oss_write`
- `ack_semantics=media_not_persisted_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_media_degradation_status_guard`

用户 copy 必须表达：媒体证据未持久化，不能作为真实 OSS/CDN external proof，需要现场 owner 补真实外部材料或修复 OSS 写入配置。

### KR6-B CDN 不可达 degraded status

当 CDN 不可达时，Robot/API/mobile 必须暴露：

- `degradation_state=media_degraded`
- `media_state=cdn_unavailable`
- `remote_ready=false`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `retry_hint=check_cdn_reachability`
- `ack_semantics=media_not_fetchable_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_media_degradation_status_guard`

用户 copy 必须表达：媒体读取不可用，缓存或本地 fixture 不能代表真实 CDN live traffic，需要真实外部 CDN evidence 后才能提高 Objective 5。

## Requirements

### P0 Robot/API Contract

Robot/API 必须提供统一、phone-safe、redacted 的媒体降级状态。状态必须让 diagnostics、operator HTTP readiness、mobile/web fixture 可以使用同一 evidence boundary。

状态中不得暴露 Authorization、bearer token、OSS AK/SK、签名 URL、bucket secret、raw traceback、本地绝对路径、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 或硬件细节。

### P0 Mobile Contract

`mobile/web` 必须展示两类只读状态：

- OSS 写失败：媒体证据未保存，主操作关闭，这不是送达成功。
- CDN 不可达：媒体证据暂不可读取，主操作关闭，这不是送达成功。

Start Delivery、Confirm Dropoff、Cancel 仍保持 disabled；不得新增 replay、resubmit、ACK、cursor、diagnostics fetch 或控制 side effect。

### P1 Documentation Contract

同步更新产品文档，明确：

- `cloud_media_degradation_status_guard`
- `software_proof_docker_cloud_media_degradation_status_guard`
- `primary_actions_enabled=false`
- `delivery_success=false`
- not real OSS/CDN live traffic
- not 真实公网 HTTPS/TLS
- not 4G/SIM
- not production DB/queue
- not real phone/browser
- not WAVE ROVER/UART/HIL
- not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved

## Priority And Acceptance

P0 验收口径：

- Robot focused tests 能证明 OSS 写失败与 CDN 不可达都输出统一 evidence boundary、fail-closed fields 和 redacted status。
- Mobile focused tests 能证明两个 fixture / UI copy 存在，且主操作仍 disabled。
- 文档检索能找到 evidence boundary、KR6 非声明边界和真实 external proof 缺口。

P1 验收口径：

- Product closeout 复核 `OKR.md` 仍保守，不把本轮写成 Objective 5 completion uplift。
- Sprint `tech-done.md`、`side2side_check.md`、`final.md` 后续由 Product 在 worker 返回后补齐。

## Responsible Engineers

- Robot Platform Engineer：Robot/API degraded status contract 与 diagnostics-safe output。
- User Touchpoint Full-Stack Engineer：mobile/web 可见状态、fixture 与用户 copy。
- Product Manager / OKR Owner：验收口径、OKR 边界、sprint 文档链路和最终收口。

## Non-Goals

本轮不是：

- 真实 OSS 写入
- 真实 CDN fetch 或 OSS/CDN live traffic
- 真实公网 HTTPS/TLS
- 4G/SIM
- production DB/queue
- production worker/migration/cutover
- 真实手机/browser
- WAVE ROVER/UART/HIL
- route/elevator field pass
- delivery result 或 delivery success
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved

