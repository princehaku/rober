# Pre-start - O7 Consumer Read Query Filters

## Sprint Type

- sprint_type: epic
- Started at: 2026-07-13 14:15 CST
- Target Objective: Objective 7, with O6 consumer-read contract support
- Owner: full-stack-software-engineer

## Latest Context

O5 remains the lowest Objective at about 85%, but the immediately previous sprint `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/` already consumed the public CDN/TLS evidence lane and closed on `blocked_http_status_not_success_class`. Re-running another O5 probe before the intended endpoint returns a success HTTP class would repeat the same support-only blocker.

O1/O3 live route execution remains gated by explicit operator approval, current live HIL / stop path, same-window LiDAR/localization/TF readiness, and Nav2/controller result capture. The recent O1/O3 sprints already packaged stop path readiness, mock stop HIL capture, route execution gate, and bounded route command plan, so this sprint must not repeat those wrappers.

O6/O7 are about 93%. Recent O6 work added archive label/task query filters, but the O7 PC consumer-read primary path still exposes only the fixed list call and does not let an operator narrow the task list by robot, task, date, status, or limit through the UI/adapter.

## Switch Reason

- Lowest Objective O5 is blocked by real external production evidence and was just probed.
- O1/O3 live execution is blocked without explicit operator-approved live safety evidence.
- This sprint chooses a non-repeating O7 consumer-read query gap that can be implemented and verified locally without hardware or production cloud.

## Non-goals

- Do not call `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or any robot movement path.
- Do not claim production cloud, real DB/queue, real OSS/CDN, real phone/browser, route execution, delivery success, HIL, or safe-to-control.
- Do not repeat O5 CDN/TLS probe, O6 archive task filters, O6 label filters, O3 replay/route packaging, or O1 stop-HIL gate packaging.
