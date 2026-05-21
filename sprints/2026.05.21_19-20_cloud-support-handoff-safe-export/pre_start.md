# Cloud Support Handoff Safe Export Pre-Start

Run time: 2026-05-21 19:20 CST

## Sprint Type

- sprint_type: epic
- capability: `cloud_support_handoff_safe_export`
- evidence boundary: `software_proof_docker_cloud_support_handoff_safe_export_gate`
- expected proof state: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- sprint folder: `sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/`

## User Value And Product North Star

The product north star is still a phone-first, low-cost ROS2 trash delivery robot that ordinary users can trust because every cloud, phone, route, elevator, hardware, and delivery claim has an explicit evidence boundary.

This sprint improves the cloud degraded-state support experience. When remote command flow is stale, backing off, unreachable, auth-failed, media-degraded, pending ACK, or requires manual takeover, the user and support operator need a phone-safe bundle they can copy without exposing credentials, raw robot internals, or success/control claims. The value is faster support triage while Start Delivery, Confirm Dropoff, and Cancel remain disabled.

## Evidence Read Before Start

- `AGENTS.md`: Epic sprint must keep real sprint records, include OKR lowest-priority checks, preserve evidence boundaries, and route execution to owner-specific Engineer agents.
- `OKR.md` 4.1, updated 2026-05-21 18:22 Asia/Shanghai: Objective 5 is the lowest at about 68%; Objective 1 is next lowest at about 81%; Objectives 2/3/4 are about 99%.
- `OKR.md` 4.1: Objective 5 still lacks real public HTTPS/TLS, 4G/SIM, true phone/browser evidence, OSS/CDN live traffic, production DB/queue connectivity, production worker/migration/cutover, and multi-instance production proof.
- Latest sprint `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/final.md`: accepted only as `software_proof_docker_field_evidence_real_material_followup_escalation_status_gate` and explicitly says "Do not repeat the same local software-proof wrapper."
- GitHub PR #5 live review-thread check on 2026-05-21: `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved; `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending.
- PR #5 comment `3269642220` is only a software-proof reply publication for `PRRT_kwDOSWB9286CJ3tX`; it is not reviewer resolution, real 2D LiDAR / ToF material, WAVE ROVER/UART proof, HIL, route/elevator field pass, or delivery success.
- GitHub PR #6 is merged but README/docs-only and does not provide runtime, hardware, cloud, phone, HIL, route/elevator, or delivery proof.
- `docs/product/mobile_user_flow.md`: degraded cloud states must keep primary actions disabled; Diagnostics and Support Handoff may remain visible while controls are blocked.
- `docs/product/cloud_4g_infrastructure.md`: cloud relay proof remains control-plane software proof; ACK does not equal delivery success, and external proof requires real HTTPS/TLS, 4G/SIM, OSS/CDN, production DB/queue, or worker/cutover evidence.

## Repeated Blocker Scan

Recent work already consumed local-only wrappers for cloud command safety, cloud hosted mobile degradation passthrough, and field-evidence real-material followup. The last final explicitly forbids another generic local wrapper.

This sprint avoids the red line by changing the product output: it does not create another blocked status rung. It creates a user/support handoff export that packages already visible degraded-state evidence into a safe, copyable support bundle. It is a functional user-support capability, but it remains Docker/local software proof and does not increase Objective 5 percentage.

## OKR Mapping

- Objective 5: direct focus. Current completion is about 68%, and this sprint targets cloud-hosted/mobile degraded-state support handoff. It must not raise the percentage because no real external cloud, 4G/SIM, OSS/CDN, production DB/queue, production worker, or true phone/browser proof arrives.
- Objective 1: about 81%, tracked as risk only. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved, and comment `3269642220` stays software-proof reply evidence only.
- Objective 2/3/4: about 99%, not the completion target. The support bundle must not claim route/elevator field pass, Nav2/fixed-route proof, real phone proof, dropoff/cancel completion, delivery result, or delivery success.

## Core Handle For This Sprint

Create `cloud_support_handoff_safe_export`: a phone-safe support handoff/export bundle for cloud degraded states. It should summarize only sanitized fields such as degraded state, blocked reason, support next step, retry hint, ACK semantics, proof boundary, redaction status, and conservative boolean flags.

The bundle must preserve:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## KR Breakdown

- KR1: Robot/API exposes a sanitized support export summary for cloud degraded states, including stale/backoff/unreachable/manual takeover/media/auth/pending ACK variants.
- KR2: Full-Stack renders a read-only mobile/web copy/export panel that is visible during degraded states and never enables primary actions.
- KR3: Autonomy performs read-only wording and evidence-boundary review so support export copy does not imply field pass, route completion, Nav2/fixed-route success, or delivery result.
- KR4: Hardware performs read-only PR #5/vendor-boundary review so support export copy does not imply `PRRT_kwDOSWB9286CJ3tX` resolution, hardware material proof, WAVE ROVER/UART proof, or HIL.
- KR5: Product closeout records actual worker evidence, updates sprint closeout docs, and updates `OKR.md` only conservatively if implementation lands; no OKR percentage increase without real external proof.

## Owners

- Product Manager / OKR Owner: product scope, PRD, OKR mapping, closeout evidence, and final conservative progress update.
- Robot Platform Engineer: safe support export summary and Robot/API diagnostics contract.
- User Touchpoint Full-Stack Engineer: mobile/web degraded-state copy/export panel.
- Autonomy Algorithm Engineer: read-only check that route/elevator/navigation wording remains `not_proven`.
- Hardware Infra Engineer: read-only check of PR #5/vendor boundary and hardware-proof language.

## Risks And Evidence Gaps

- O5 remains blocked for completion until real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, production worker/cutover, or true phone/browser evidence exists.
- The export bundle may make support triage easier, but it is still `software_proof_docker_cloud_support_handoff_safe_export_gate`, not real cloud proof.
- Phone copy must not expose raw ROS topics, `/cmd_vel`, serial/UART paths, baudrate values, WAVE ROVER parameters, Authorization headers, bearer tokens, credentials, DB/queue URLs, OSS AK/SK, local paths, tracebacks, checksums, complete artifacts, raw GitHub material, or raw robot responses.
- The implementation must not turn Support Handoff into a control path, retry endpoint, ACK/cursor request, automatic replay, or GitHub action.

## Sprint Documents To Create Or Update

Created during planning:

- `sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/pre_start.md`
- `sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/prd.md`
- `sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/tech-plan.md`

Required after worker implementation:

- `sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/tech-done.md`
- `sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/side2side_check.md`
- `sprints/2026.05.21_19-20_cloud-support-handoff-safe-export/final.md`
- `OKR.md` and `docs/process/okr_progress_log.md` only during Product closeout if implementation evidence lands; Objective 5 percentage remains unchanged unless real external proof arrives.
