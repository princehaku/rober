# Pre Start - O5 CDN/TLS Readiness Packet Consumption

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_19-19_o5_cdn_tls_readiness_packet_consumption/`
- started_at: 2026-07-13 19:19 CST
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target Objective: O5 cloud relay productionization
- Direction judgment: continue O5 without repeating the same CDN 4xx probe

## User Value And Product North Star

普通手机用户最终需要通过公网云入口查看任务状态和只读证据，而不是依赖本地 mock 或工程人员手动拼材料。13:13 sprint 已经拿到真实外部 TLS/cert observation，但没有进入 O5 production cutover readiness packet；运营仍无法在同一个 readiness artifact 中看到“公网 TLS 已观测、HTTP 仍 4xx blocked”的事实。

本轮北极星仍是普通用户把垃圾交给小车后，通过云端控制面和证据链安全完成固定路线送达。本 sprint 只推进 O5 readiness 证据消费，不触碰 route execution、delivery、HIL、`/cmd_vel`、`/api/base/manual`、NavigateToPose 或 WAVE ROVER UART。

## Background

当前最低 Objective 是 O5，约 `85%`。最近 O5 sprint `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/` 已真实访问默认 CDN/TLS target，artifact 记录：

- `probe_attempted=true`
- `external_request_attempted=true`
- `tls_handshake_observed=true`
- `certificate_valid_for_host=true`
- `http_method=HEAD`
- `http_status_class=4xx`
- `cdn_tls_external_evidence_status=blocked_http_status_not_success_class`
- `accepted_claim=none`

直接重跑该 probe 会重复消费 `blocked_http_status_not_success_class`。本轮改为让 O5 production cutover readiness packet 机读消费该 sanitized artifact，把真实 TLS/cert observation 纳入 readiness 汇总，同时继续 fail closed。

## Non-Repeating Blocker Reason

本 sprint 不重复 13:13 CDN/TLS 4xx blocker，原因：

- 不重新请求同一 CDN path。
- 不把 4xx 解释为 O5 production readiness。
- 只新增 readiness packet 对既有 sanitized external evidence artifact 的消费能力。
- 如果 artifact 仍是 4xx，packet section 必须 `blocked_not_proven` 或等价 fail-closed 状态，并保留 `accepted_claim=none`。

## Needed Work

`robot-software-engineer` 需要：

- 增加 O5 CDN/TLS external evidence summary validator/summary helper，消费 `trashbot.o5.cdn_tls_external_evidence.v1` artifact。
- 将该 artifact 作为 `cloud_production_cutover_readiness_packet` 的一个独立 source slot。
- 增加 CLI/env consumption 入口，例如 `TRASHBOT_REMOTE_CLOUD_CDN_TLS_EXTERNAL_EVIDENCE_ARTIFACT` 和 preflight/packet path。
- 更新测试，覆盖 4xx artifact 被 packet 消费但继续 blocked、不泄漏 URL/path/token/raw header/traceback/local path、dangerous true fail closed。
- 同步更新 `docs/product/cloud_4g_infrastructure.md` 和 O5 interface 文档。
- 更新本 sprint `tech-done.md`，记录实际改动、验证结果、失败定位和剩余风险。

## Acceptance Boundary

接受为：

- O5 CDN/TLS external evidence readiness packet consumption software proof.
- 真实 TLS/cert observation 被 O5 cutover packet 机读消费。
- 仍保留 support-only / fail-closed 边界。

拒绝为：

- production cloud ready.
- OSS object upload 或 CDN origin fetch.
- production DB/queue 或 worker cutover.
- 4G/SIM.
- real phone/browser proof.
- route execution、delivery success、HIL 或 safe-to-control.
