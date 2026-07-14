# Pre Start - O5 CDN/TLS External Evidence Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target Objective: O5 cloud relay productionization
- Planning status: ready for Robot Software implementation
- Direction judgment: continue O5 with a narrow external evidence delta

## User Value And Product North Star

普通手机用户最终只应看到可靠的一键发车、状态查看和异常提示，不需要理解 ROS2、SSH、串口、OSS 或 CDN。O5 的用户价值是证明云中转与公开只读入口有真实公网可达性基础，避免手机端体验只停留在 local/mock 控制面。

本 sprint 的产品北极星仍是固定路线垃圾投递机器人：用户交付垃圾后，小车能通过云端控制面和可回看的证据链完成任务。本轮只补 O5 的公网 CDN/TLS external evidence，不触碰 route execution、delivery 或 safe-to-control。

## Background

当前 `OKR.md` 中 O5 约 `85%`，主要缺口是：

- 真实公网 HTTPS/TLS。
- 真实 4G/SIM。
- production DB/queue。
- production worker/cutover。
- OSS/CDN live traffic。
- 真实手机/browser 证据。

最近两轮 sprint 已经连续推进 O6 query filter 合同：

- `sprints/2026.07.13_11-13_o6_o7_label_query_filters/`：label list local/mock filter hardening。
- `sprints/2026.07.13_12-13_o6_archive_task_query_filters/`：archive task list local/mock filter hardening。

这两轮都不是 O5 external production evidence。继续做 O6 query filter、readback wrapper、safe summary、handoff 或 intake surface，会重复消费同一类 support-only 软件证据，不能推动 O5 当前主要缺口。

## Core Lever

规划一个由 `robot-software-engineer` 实现的真实外部 CDN/TLS probe：

- 默认目标来自 `OKR.md` KR4 的公开 CDN base URL；允许通过环境变量覆盖 probe target。
- probe 必须真实发起外部 HTTPS/TLS 请求，优先使用 `HEAD`，必要时可降级为 bounded `GET`。
- artifact、preflight、summary 不得保存完整 URL、token、响应体、路径、query、header secret、cookie、credential、原始异常栈或本地绝对路径。
- 只允许保存红线内的短摘要，例如 target source、scheme、host hash prefix、TLS/cert booleans、HTTP status class、elapsed bucket、content-length bucket、safe error class、blocked reasons、`next_live_command`。

## Product Acceptance Position

如果实际外部 probe 成功，Product 只接受为：

- O5 CDN/TLS external evidence delta。
- `cdn_tls_external_evidence` 类 evidence。
- 真实公网 HTTPS/TLS 与 CDN endpoint reachability 的窄证据。

Product 明确拒绝把本 sprint 解释为：

- production cloud ready。
- OSS object upload 成功。
- CDN origin fetch 成功。
- production DB/queue 成功。
- production worker/cutover 成功。
- 真实 4G/SIM 成功。
- 真实手机/browser 验收成功。
- route execution 或 delivery success。
- safe-to-control。

固定安全边界必须写入 artifact 和 closeout：

- `delivery_success=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `hil_pass=false`

## Non-Repeating Blocker Reason

本 sprint 不是继续消费最近两轮 O6 query filter blocker，理由如下：

- Objective 切回当前最低项 O5，而不是继续 O6/O7 local/mock query contract。
- 核心证据从 file-backed archive/readback 变成真实外部 CDN/TLS probe。
- 成功只计 external evidence delta；失败也必须 fail closed 并给出下一条 live command，而不是再生成 wrapper packet。
- 不把 `support_only_reason=no_real_production_external_evidence` 重写成新的进度；只有外部 probe 真实执行并产生 sanitized artifact，才算本轮有效增量。

## KR Breakdown And History Judgment

- 当前推进 KR：O5 KR4，公开 CDN base URL 作为只读入口，私有数据仍走 API 网关 + bearer。
- 本轮不新增 KR，不归档 KR。
- 已完成 KR 历史记录位置：本轮 planning 不移动历史区；后续只有在 `tech-done.md`、`side2side_check.md`、`final.md` 存在真实外部 probe evidence 且 Product 接受后，才考虑在 `OKR.md` 中追加阶段证据。
- 剩余风险：即使 probe 成功，也只说明 CDN/TLS endpoint reachability，不说明 production cloud 或 delivery 闭环。

## Needed Work

`robot-software-engineer` 需要实现一个可重复运行的外部 probe 和最小测试：

- 外部 probe command。
- sanitized summary artifact。
- fail-closed preflight/summary handling。
- unit tests 覆盖成功、TLS/HTTP failure、unsafe input、URL/token/body/path redaction。
- sprint `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险。

## Priority And Acceptance

Priority: P0 for current O5 planning because O5 是最低 Objective，且真实 production/cloud evidence 是主要缺口。

Product acceptance gate:

- 实际发起外部 HTTPS/TLS probe，或在网络/TLS 不可用时 fail closed。
- artifact 包含 `cdn_tls_external_evidence`、`next_live_command`、`delivery_success=false`、`safe_to_control=false`。
- artifact 不包含完整 URL、token、response body、path、credential、cookie、raw header、traceback 或本地绝对路径。
- 成功时只接受 O5 CDN/TLS external evidence delta；失败时必须给出下一条 live command。

## Sprint Docs To Create Or Update

Planning phase creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Implementation phase must later create or update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
