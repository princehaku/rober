# Side By Side Check - O5 CDN/TLS External Evidence Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Product status: accepted fail-closed, no OKR percentage lift

## User Value And Product North Star

普通手机用户最终需要一个不依赖 SSH、ROS2 或局域网直连的公开只读入口。本轮的用户价值是确认 O5 的公网 CDN/TLS 入口链路至少触达了真实外部 HTTPS/TLS 与证书校验层；但该价值仍停在入口观测，不等于生产云、手机浏览器或送达任务闭环。

北极星仍是固定路线垃圾投递机器人：用户交付垃圾后，小车通过云端控制面和证据链完成送达。本轮只验收 O5 external CDN/TLS evidence probe，不验收路线执行、投递、HIL 或 safe-to-control。

## Side By Side Acceptance

| Gate | Expected | Observed | Product decision |
| --- | --- | --- | --- |
| Evidence schema | `trashbot.o5.cdn_tls_external_evidence.v1` | `schema=trashbot.o5.cdn_tls_external_evidence.v1` | pass |
| Evidence key | `cdn_tls_external_evidence` | `evidence_key=cdn_tls_external_evidence` | pass |
| External request | Real external probe attempted | `probe_attempted=true`, `external_request_attempted=true` | pass |
| TLS and cert | Useful external TLS/cert observation | `tls_handshake_observed=true`, `certificate_valid_for_host=true` | pass |
| HTTP result | Success class required for accepted claim | `http_method=HEAD`, `http_status_class=4xx` | fail closed |
| Product claim | Do not over-claim when HTTP is non-success | `cdn_tls_external_evidence_status=blocked_http_status_not_success_class`, `accepted_claim=none` | accepted as blocked |
| Safety invariants | Keep all control/delivery/HIL fields false | `delivery_success=false`, `safe_to_control=false`, `robot_control_executed=false`, `route_execution_success=false`, `hil_pass=false` | pass |
| Redaction | No URL/path/query/body/raw header/traceback/local path | `redaction_status.status=pass` with omitted markers true | pass |

## OKR Mapping And Direction Judgment

- O5: continue, but no percentage lift. The sprint produced a useful TLS/cert observation, yet HTTP remained `4xx` and `accepted_claim=none`.
- O1: unchanged at about `94%`; no HIL, route execution, delivery, or safe-to-control evidence was produced.
- O6/O7: unchanged at about `93%`; this is not archive/readback or PC consumer progress.
- KR archival: `不归档`. KR4 remains current because CDN/TLS did not reach a success HTTP class and did not prove production cloud readiness.

Direction judgment: continue O5 only when the next run can produce successful external CDN/TLS/public ingress evidence or stronger production evidence. If that cannot be obtained, pivot to explicit operator-approved current live HIL/current route evidence rather than repeating support-only wrappers.

## Rejected Claims

This sprint explicitly rejects:

- production cloud ready.
- OSS object upload.
- CDN origin fetch.
- production DB/queue.
- production worker cutover.
- 4G/SIM.
- real phone/browser.
- route execution.
- delivery success.
- HIL.
- safe-to-control.

## Risk And Evidence Gap

The remaining blocker is exact and narrow: `blocked_http_status_not_success_class`. TLS handshake and certificate validation were observed, but the endpoint returned `http_status_class=4xx`, so Product cannot accept `cdn_tls_external_evidence` as an OKR-lifting external production proof.

Next required evidence: rerun the same sanitized probe against an intended public CDN base that returns a success HTTP class, then separately prove OSS upload/origin fetch, production DB/queue, worker cutover, 4G/SIM, and real phone/browser paths before any production-ready claim.
