# PRD - O5 CDN/TLS External Evidence Probe

## Product Goal

把 O5 从 local/mock cloud relay confidence 推进到一个真实外部 CDN/TLS external evidence delta。用户价值不是多一个内部状态面板，而是确认普通手机未来要访问的公开只读入口具备最小公网 HTTPS/TLS 可达性证据。

## North Star Fit

rober 的北极星是面向普通手机用户的固定路线垃圾投递机器人。O5 支撑的是手机用户不需要 SSH、ROS2 或局域网直连，也能通过云端入口查看任务状态和证据。CDN/TLS probe 是这条链路的公网入口证据，但不是任务执行证据。

## Users And Stakeholders

- Primary user: 普通手机用户，未来通过公开入口或手机 UI 查看任务状态和只读证据。
- Product owner: `product-okr-owner`，负责 O5 验收口径和 OKR 边界。
- Implementation owner: `robot-software-engineer`，负责 probe、artifact、测试和 `tech-done.md`。
- Future consumers: O6/O7 只能消费 sanitized summary，不得依赖完整 URL、响应体或凭证。

## Problem

O5 目前约 `85%`，已经有本地 relay、SQLite shadow、local/mock endpoint probe、cutover readiness packet 等软件证据，但主要缺口仍是外部 production/cloud evidence。最近两轮 O6 query filter 只是 local/mock contract hardening，不能继续替代 O5 的公网入口证据。

## Scope

In scope:

- 一个真实外部 CDN/TLS probe。
- 默认目标从 `OKR.md` KR4 的公开 CDN base URL 读取或在代码中使用该公开默认值。
- 允许环境变量覆盖目标，以便临时指向 staging/public CDN。
- 生成 sanitized artifact 和 summary。
- 成功、失败和 unsafe input 都 fail closed 或输出明确边界。
- 输出 `next_live_command`，并且不泄漏完整 URL、token、响应体、路径或凭证。

Out of scope:

- OSS object upload。
- CDN origin fetch 证明。
- production DB/queue。
- production worker/cutover。
- 4G/SIM。
- 真实手机/browser。
- route execution。
- delivery success。
- safe-to-control。

## Functional Requirements

1. Probe command
   - Provide a CLI or script runnable by `robot-software-engineer`.
   - Default target is the O5 KR4 public CDN base URL from `OKR.md`.
   - Optional env override supports external validation without code edits.
   - Use HTTPS only for accepted success; non-HTTPS target must fail closed.

2. Sanitized artifact
   - Emit a JSON artifact with schema similar to `trashbot.o5.cdn_tls_external_evidence.v1`.
   - Include `cdn_tls_external_evidence_status`, `probe_attempted`, `external_request_attempted`, `tls_handshake_observed`, `certificate_valid_for_host`, `http_status_class`, `elapsed_ms_bucket`, `content_length_bucket`, `blocked_reasons`, and `next_live_command`.
   - Include fixed false fields: `delivery_success=false`, `safe_to_control=false`, `robot_control_executed=false`, `route_execution_success=false`, `hil_pass=false`.
   - Store target source and safe hostname hash prefix, not complete endpoint material.

3. Redaction and safety
   - Do not write full URL, path, query, token, bearer, cookie, response body, raw response headers, credential material, raw traceback, or local absolute path to artifact, preflight, summary, logs intended for sprint evidence, or O6/O7 summaries.
   - Unsafe target input fails closed with a sanitized reason.
   - Error output should use short classes such as `dns_failed`, `tls_failed`, `http_timeout`, `http_non_2xx_3xx`, `unsafe_target`, or `network_unavailable`.

4. Acceptance semantics
   - Success means: external HTTPS/TLS CDN endpoint was reached enough to produce a sanitized status class.
   - Failure means: no O5 credit; artifact must preserve blocker and next live command.
   - Neither case may claim production cloud, OSS upload, CDN origin fetch, DB/queue, 4G/SIM, real phone/browser, route execution, delivery, HIL, or safe-to-control.

## Product Acceptance Criteria

Product accepts the implementation only if:

- The evidence contains `cdn_tls_external_evidence`.
- The implementation owner is `robot-software-engineer`.
- The probe can target the OKR KR4 public CDN base URL or environment override.
- The acceptance artifact contains `next_live_command`.
- The artifact and summary contain `delivery_success=false` and `safe_to_control=false`.
- The artifact is sanitized: no full URL, token, response body, path, credential, cookie, raw header, traceback, or local absolute path.
- `tech-done.md` reports actual changed files, verification commands, failure positioning, and remaining risk.

## OKR Mapping And Direction Judgment

- O5: continue. This is the lowest Objective and the sprint targets its main external evidence gap.
- O6/O7: pause for this sprint. Recent O6 query filters are useful but repeating them would not close O5.
- O1/O3: not targeted. Route execution, delivery and HIL remain outside this sprint.
- KR archival: no KR is archived during planning. After implementation, Product may record a narrow O5 CDN/TLS external evidence delta, but only if the external probe really ran and passed the redaction gate.

## Evidence Chain Needed

Minimum acceptable evidence chain:

1. Command invocation with sanitized target source.
2. Probe summary JSON with `cdn_tls_external_evidence`.
3. Redaction self-check showing no complete URL, token, body, path, credential, cookie, raw header, traceback or absolute local path is persisted.
4. Unit tests or smoke tests for success and fail-closed behavior.
5. `tech-done.md` plus later `side2side_check.md` and `final.md` with accepted/rejected claims.

## Risks And Blockers

- External network may be unavailable on the development host or CI.
- CDN target may return 403/404 while TLS is valid; Product may still accept only the observed narrow status, not production readiness.
- Environment override could contain secret material; implementation must never persist it.
- Full URL redaction is mandatory even though the default CDN base is public, because the same path will be reused with private or staging targets.
