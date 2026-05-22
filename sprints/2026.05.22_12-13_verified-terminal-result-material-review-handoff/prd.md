# Verified Terminal Result Material Review Handoff PRD

Run time: 2026-05-22 12:13 Asia/Shanghai

## User Value

When support or a field owner has only metadata about a terminal delivery/dropoff/cancel result, they need a clear handoff package rather than another ambiguous pending status. This sprint makes the missing terminal-result material actionable: who owns the next step, what real evidence must be supplied, and why the current state is still not delivery success.

## OKR Mapping

- Primary Objective: Objective 5, because it remains the lowest at about 68%.
- Secondary constraints: Objective 2/3 terminal result and route/elevator evidence must not be claimed without real task records, route logs, or field pass material.
- PR #5 / Objective 1 remains a separate unresolved hardware-material thread and must not be marked resolved by this work.

## Product Requirements

1. PC gate consumes `verified_terminal_result_material_review_decision` output and emits `verified_terminal_result_material_review_handoff`.
2. Handoff output must include safe `evidence_ref`, terminal result type, prior review decision, owner handoff, missing/rejected/accepted material summary, next required evidence, safe copy, and fail-closed flags.
3. Robot diagnostics must expose only a sanitized safe alias: `robot_diagnostics_verified_terminal_result_material_review_handoff_summary`.
4. Mobile/web must show a read-only handoff panel with safe copy/export support and no control enablement.
5. Missing, unsupported, unsafe, success-claiming, raw, credential-bearing, local-path-bearing, ROS/control, hardware, or reviewer-resolution input must fail closed.
6. Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, replay, resubmit, raw diagnostics fetch, and robot commands must remain disabled.

## Acceptance Boundary

Accepted output is `software_proof_docker_verified_terminal_result_material_review_handoff_gate` only.

The sprint must explicitly say it is not:

- real external cloud proof
- public HTTPS/TLS proof
- 4G/SIM proof
- OSS/CDN live traffic proof
- production DB/queue or worker/cutover proof
- true phone/browser proof
- route/elevator field pass
- Nav2/fixed-route proof
- dropoff/cancel completion
- verified terminal delivery/dropoff/cancel result
- WAVE ROVER/UART/HIL proof
- PR #5 reviewer resolution
- delivery success

## Documentation Requirements

- PC contract docs / README must describe the new handoff gate.
- Robot diagnostics docs must describe the safe alias and fail-closed behavior.
- Mobile user-flow docs must describe the read-only panel and proof boundary.
- Sprint closeout must update `OKR.md` and `docs/process/okr_progress_log.md` conservatively after validation evidence is available.
