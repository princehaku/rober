# Cloud Support Handoff Safe Export PRD

Run time: 2026-05-21 19:20 CST

## User Value

When the robot is in a cloud degraded state, a normal user should not need SSH, ROS2 commands, GitHub context, raw diagnostics, or cloud credentials to explain the failure to support. They need a safe copy/export bundle that says what happened, why controls are disabled, what support should do next, and what evidence boundary applies.

The user-facing value is safe escalation: support gets enough structured context to triage remote failure, manual takeover, stale status, backoff, auth failure, media degradation, or pending ACK without exposing raw internals or implying the robot succeeded.

## Product North Star

The north star remains a trustworthy phone-first trash delivery robot. Trust means the phone can say "not proven yet" clearly when cloud status is degraded, and the product never converts ACK, stale status, manual takeover, or a support export into delivery success.

This sprint is a functional support handoff improvement for Objective 5, but it remains Docker/local software proof.

## Problem Statement

Objective 5 is still the lowest at about 68%, but the repo has repeatedly hit the same no-real-external-proof blocker: no public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser evidence.

The last sprint completed only `software_proof_docker_field_evidence_real_material_followup_escalation_status_gate` and warned not to repeat the same local software-proof wrapper. The next useful O5 move is therefore not another readiness flag. It is a phone-safe support export for degraded cloud states so user/support triage improves while control remains disabled.

## OKR Mapping

- Objective 5: primary target. Build `cloud_support_handoff_safe_export` for degraded cloud states. No percentage increase without real external cloud or true phone/browser proof.
- Objective 1: tracked as a guardrail. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending; comment `3269642220` is not reviewer resolution or hardware proof.
- Objective 2: guardrail only. The export must not imply delivery result, dropoff completion, cancel completion, elevator success, or delivery_success=true.
- Objective 3: guardrail only. The export must not imply Nav2/fixed-route field pass, route completion signal, or real route runtime proof.
- Objective 4: support surface. The phone panel may copy safe diagnostics but must not claim true iPhone/Android proof, production app proof, PWA prompt/userChoice, or real browser proof.

## KR Breakdown

| KR | Product Requirement | Evidence Boundary |
| --- | --- | --- |
| KR1 | Produce a sanitized cloud support export summary for degraded states. | `software_proof_docker_cloud_support_handoff_safe_export_gate` |
| KR2 | Mobile/web displays a read-only copy/export panel for support handoff. | `safe_to_control=false`, `primary_actions_enabled=false` |
| KR3 | Export includes degraded state, blocked reason, support next step, retry hint, ACK semantics, redaction status, and proof boundary. | `source=software_proof`, `not_proven` |
| KR4 | Export excludes raw diagnostics, credentials, ROS/serial/hardware details, DB/queue/OSS secrets, local paths, checksums, and complete artifacts. | phone-safe whitelist only |
| KR5 | Product closeout preserves Objective 5 at about 68% unless real external proof arrives. | no OKR inflation |

## Scope

In scope:

- Define capability `cloud_support_handoff_safe_export`.
- Support degraded states including `status_stale`, `cloud_poll_backoff`, `cloud_unreachable`, `manual_takeover_required`, `command_pending`, `auth_failed`, and `media_degraded`.
- Create a Robot/API safe support export summary with `software_proof_docker_cloud_support_handoff_safe_export_gate`.
- Create a mobile/web read-only panel that copies/export only safe support metadata.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Record PR #5 and PR #6 boundaries so hardware/docs-only evidence is not mistaken for runtime or cloud proof.

Out of scope:

- Real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/migration/cutover, or multi-instance proof.
- True iPhone/Android browser validation, production app proof, PWA prompt/userChoice proof, or real phone acceptance.
- HIL, WAVE ROVER/UART proof, real 2D LiDAR / ToF material proof, or PR #5 reviewer resolution.
- Real route/elevator field pass, Nav2/fixed-route runtime proof, dropoff/cancel completion, delivery result, or delivery success.
- Any endpoint that retries, replays, resubmits, requests ACK/cursor, controls the robot, posts to GitHub, or changes hardware configuration.

## Priority

P0:

- Preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Include required evidence references: Objective 5, Objective 1, `PRRT_kwDOSWB9286CJ3tX`, `3269642220`, `cloud_support_handoff_safe_export`, and `software_proof_docker_cloud_support_handoff_safe_export_gate`.
- Provide a clear phone-safe copy/export bundle for support.

P1:

- Support multiple degraded states with stable labels and recovery hints.
- Keep export whitelist-based and predictable enough for support to paste into an issue, ticket, or field handoff.
- Keep Chinese-first user copy clear that this is not delivery success.

P2:

- Product closeout should update `OKR.md` only after implementation evidence lands, with Objective 5 unchanged unless real external proof is supplied.

## Acceptance Criteria

- Planning docs exist for the new Epic sprint folder.
- Tech plan includes `## OKR 最低优先级核对`.
- Downstream implementation plan names parallel owners: Robot/API, Full-Stack, Autonomy read-only, Hardware read-only, and Product closeout.
- Capability `cloud_support_handoff_safe_export` and boundary `software_proof_docker_cloud_support_handoff_safe_export_gate` are used consistently.
- The sprint references Objective 5, Objective 1, `PRRT_kwDOSWB9286CJ3tX`, and `3269642220`.
- All outputs preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.
- The plan explicitly says PR #6 is README/docs-only and does not provide runtime, hardware, cloud, or phone proof.

## Safe Export Requirements

Allowed export fields should be whitelisted:

- schema and schema version;
- capability;
- degraded state and safe display label;
- blocked reason;
- support next step;
- retry hint;
- ACK semantics;
- proof boundary;
- redaction status;
- conservative flags: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `not_proven`;
- safe evidence references such as Objective 5, Objective 1, `PRRT_kwDOSWB9286CJ3tX`, and `3269642220`.

The export must not include raw ROS topics, `/cmd_vel`, serial/UART paths, baudrate values, WAVE ROVER parameters, Authorization headers, bearer tokens, GitHub tokens, DB/queue URLs, OSS AK/SK, credential-bearing URLs, local paths, tracebacks, checksums, complete artifacts, raw robot responses, raw diagnostics, raw GitHub review bodies, or success/control copy.

## Responsibility

- Product Manager / OKR Owner: PRD, OKR mapping, scope, sprint closeout, and conservative progress language.
- Robot Platform Engineer: safe support export summary, schema/gate, Robot diagnostics contract, and focused validation.
- User Touchpoint Full-Stack Engineer: mobile/web panel, fixture, copy/export behavior, and focused validation.
- Autonomy Algorithm Engineer: read-only wording/evidence review for route/elevator/navigation non-claims.
- Hardware Infra Engineer: read-only PR #5/vendor-boundary review and hardware non-claim confirmation.

## Risks And Blockers

- This sprint cannot advance Objective 5 completion percentage without real external proof.
- A poorly scoped export could leak sensitive internals or create a false control path.
- Copy that sounds too optimistic could make users think delivery, cloud, phone, route/elevator, or HIL proof exists.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved until real hardware/vendor materials and reviewer resolution arrive.
