# PRD - O5 CDN/TLS Readiness Packet Consumption

## Product Goal

把 13:13 的 sanitized CDN/TLS external evidence artifact 接入 O5 production cutover readiness packet，使 O5 主 readiness artifact 能表达“公网 TLS/cert 已观测，但 HTTP success class 未达成”的状态。

## Problem

当前 O5 readiness packet 已聚合 deployment、external probe、public ingress/TLS、DB/queue、worker rehearsal、cutover drain、OSS/CDN live probe 和 external evidence intake，但没有消费新的 `trashbot.o5.cdn_tls_external_evidence.v1` artifact。

这导致 Product closeout 虽然知道 TLS/cert observation 存在，preflight/cutover packet 仍无法用同一机读合同展示该事实。

## Scope

In scope:

- 新增 CDN/TLS external evidence artifact summary/validation。
- 将该 summary 纳入 cloud production cutover readiness packet source slots。
- preflight 或 CLI path 能通过环境变量/参数消费该 artifact。
- 测试 4xx blocked artifact、安全 artifact、hostile artifact。
- 文档同步。

Out of scope:

- 再次真实访问 CDN endpoint。
- 更改 CDN target 或绕过 13:13 blocker。
- 真实 OSS 上传、CDN 回源、DB/queue、worker cutover、4G/SIM、手机浏览器验收。
- 任何机器人控制或硬件动作。

## Functional Requirements

1. Artifact summary
   - 接受 schema `trashbot.o5.cdn_tls_external_evidence.v1`。
   - 验证 `evidence_key=cdn_tls_external_evidence`。
   - 验证 fixed false fields 仍为 false。
   - 提取安全字段：TLS/cert booleans、HTTP status class、method、status、accepted claim、blocked reasons、target host hash prefix presence。
   - 不复制完整 URL、path、query、response body、raw headers、token、cookie、traceback、本地绝对路径。

2. Readiness packet source
   - 新 source name 建议为 `cdn_tls_external_evidence`。
   - 新 env var 建议为 `TRASHBOT_REMOTE_CLOUD_CDN_TLS_EXTERNAL_EVIDENCE_ARTIFACT`。
   - Packet `artifact_counts.artifact_slots` 必须随 source 增加。
   - 4xx artifact 可被读取，但 section 必须保持 `blocked_not_proven` 或等价 fail-closed，不能变成 production ready。

3. CLI/preflight
   - Packet write path 和 preflight path 均可消费该 env/arg。
   - 如果只提供 CDN/TLS artifact，packet 也可生成，`software_proof_ready=true` 仅代表 support-only readiness。

4. Safety
   - Hostile artifact 中任何 dangerous true、URL、token、local path、raw response、traceback 必须 fail closed。
   - Packet 和 preflight 输出不得泄漏 artifact absolute path。

## Product Acceptance Criteria

- Targeted unit tests pass.
- `py_compile` pass.
- Generated packet artifact contains `cdn_tls_external_evidence` source slot.
- 13:13 4xx artifact is consumed as blocked/not proven, not OKR-lifting proof.
- Fixed false fields remain false.
- Docs and `tech-done.md` are updated.

## OKR Mapping

O5 remains the lowest Objective at about `85%`. This sprint targets O5 directly, but Product will not raise percentage unless the consumed evidence reaches success-class public endpoint or stronger production evidence. With the existing 4xx artifact, expected result is useful O5 readiness consumption without KR archival.
