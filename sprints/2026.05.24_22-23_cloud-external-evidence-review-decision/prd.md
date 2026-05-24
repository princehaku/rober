# PRD - Cloud external evidence review decision

- sprint_type: epic
- sprint: `2026.05.24_22-23_cloud-external-evidence-review-decision`
- target capability: `cloud_external_evidence_review_decision`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_decision_gate`
- source capability: `trashbot.external_evidence_intake`

## Product Problem

Objective 5 is still lowest at about 68%, but the repo has already spent multiple sprints proving local Docker support metadata. The latest final says the next lift requires real external or hardware evidence, not another local-only wrapper. At the same time, the existing `trashbot.external_evidence_intake` gate only provides a safe intake shape for future public HTTPS/TLS, 4G/SIM, OSS/CDN and production DB/queue materials; it does not give support a review decision that says whether the intake is acceptable, incomplete, unsafe, or blocked.

Without a review-decision layer, future real materials can arrive but remain hard to classify consistently. That keeps O5 blocked even when evidence starts appearing, and it tempts the team to keep adding local status wrappers that carry `no OKR percentage lift`.

## User Value

Support, field operators and reviewers need one fail-closed place to answer:

- Did a safe external-evidence intake artifact exist?
- Which O5 material families are present, missing or unsafe?
- Was any submitted material rejected because it contains credentials, raw URLs, DB/queue endpoints, OSS secrets, response bodies, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, or hardware claims?
- What exact next evidence is needed before Objective 5 can claim real external proof?

This helps the ordinary phone user indirectly: the phone UI can explain "waiting for external cloud evidence review" instead of making the primary action look available.

## Product North Star

`rober` should be a phone-first trash delivery robot that works through cloud relay without requiring the phone and robot to share WiFi. O5 is the productization path for that cloud relay. This sprint advances the evidence review workflow needed for that path while preserving the current Docker-only boundary.

## OKR Mapping

| OKR | Mapping |
| --- | --- |
| Objective 5 KR1 | Helps review whether cloud commands/status/ack deployment evidence exists, without exposing `/cmd_vel` or inbound robot control. |
| Objective 5 KR2 | Keeps cloud infrastructure evidence tied to `docs/product/cloud_4g_infrastructure.md` and `docs/product/remote_4g_mvp.md`. |
| Objective 5 KR3/KR4 | Reviews OSS/CDN evidence family as redacted metadata only; no secret or full URL output. |
| Objective 5 KR5 | Explicitly rejects credential-bearing or raw endpoint materials. |
| Objective 5 KR6 | Keeps graceful degradation visible when external materials are missing or unsafe. |

No OKR percentage lift is planned in this sprint because the host has Docker only and no real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result, HIL, or hardware proof.

## KR Breakdown For This Sprint

1. Create `cloud_external_evidence_review_decision` as a software-only review decision over existing external evidence intake summaries.
2. Preserve `software_proof`, `not_proven`, `production_ready=false`, `overall_status=blocked`, `external_evidence_complete=false`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `no OKR percentage lift`.
3. Add a Robot/API safe summary that mobile can consume without raw artifacts or robot-control side effects.
4. Add a `mobile/web` read-only panel that shows the review decision and next required evidence while keeping all primary actions disabled.
5. Update relevant docs after implementation so `docs/` reflects the new capability.

## Requirements

The implementation must:

- Consume only safe fields from the existing external evidence intake artifact or summary.
- Emit a deterministic decision state: accepted, needs backfill, rejected unsafe, blocked missing intake, or evidence-ref mismatch.
- Keep PR #5 thread `PRRT_kwDOSWB9286CJ3tX` visible only as unresolved / `hardware_material_pending` context and never imply PR #5 resolution.
- Make unsupported or missing material families explicit: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof and verified terminal result.
- Reject unsafe raw data and credentials by design.
- Avoid any command, ACK/cursor mutation, GitHub mutation, material upload, replay/resubmit, raw diagnostics fetch, or robot-control route.
- Use focused tests only; no broad regression or Docker build unless an Engineer proves it is needed.

## Non Requirements

This sprint does not:

- Run public probes against a real domain.
- Prove TLS, DNS, firewall or reverse-proxy routing.
- Prove 4G/SIM connectivity.
- Prove OSS upload, CDN cache hit or CDN live traffic.
- Prove production DB/queue connectivity, ordering, migration, worker or cutover.
- Prove true phone/browser behavior on iPhone/Android.
- Resolve PR #5 `PRRT_kwDOSWB9286CJ3tX`.
- Touch WAVE ROVER, UART, serial, LiDAR/ToF, HIL, Nav2/fixed-route runtime or delivery success.

## Acceptance Criteria

The sprint can close only if:

- The new summary/panel/gate all use `cloud_external_evidence_review_decision` and `software_proof_docker_cloud_external_evidence_review_decision_gate`.
- Review states are deterministic and tested.
- The mobile panel renders fail-closed and keeps Start Delivery, Confirm Dropoff, and Cancel disabled.
- Robot/API safe alias does not leak raw artifacts, credentials, endpoints, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER or hardware details.
- Focused validation commands in `tech-plan.md` pass.
- Product closeout records that this is Docker `software_proof`, not true phone/browser proof, not O5 external proof, not delivery success, and `no OKR percentage lift`.

## Risks And Evidence Gaps

- Real O5 lift still depends on external materials that are not available on this Docker-only host.
- The capability could be misread as external proof if copy is loose; every surface must say `not_proven` and `no OKR percentage lift`.
- If Engineers find `trashbot.external_evidence_intake` already has a compatible review-decision layer, they should report that and pivot to the smallest missing gap rather than duplicate it.
- Hardware-adjacent references remain blocked by `hardware_material_pending`; this sprint does not authorize hardware conclusions.
