# Verified Terminal Result Material Followup Escalation Status PRD

Run time: 2026-05-23 12:05 Asia/Shanghai

## User Value And Product North Star

When a field owner, support owner, or reviewer receives a verified terminal-result material handoff, they need a clear next action instead of another ambiguous pending state. This sprint gives them a follow-up escalation status that says whether terminal result material is still missing, whether support ownership must change, whether the follow-up is unsafe, or whether the source handoff is missing.

The product north star is still a normal-phone-user trash delivery flow with conservative proof boundaries: support can explain the state and ask for the right evidence, but the system does not unlock Start Delivery, Confirm Dropoff, Cancel, ACK mutation, or success copy without real verified material.

## OKR Mapping

- Primary Objective: Objective 5, because `OKR.md` 4.1 keeps cloud relay / OSS/CDN data path productization lowest at about 68%.
- Terminal-result KR focus: make missing verified terminal delivery/dropoff/cancel result material reviewable and escalatable after `verified_terminal_result_material_review_handoff`.
- Secondary Objective 2/3/4 constraints: this work must not claim route/elevator field pass, Nav2/fixed-route runtime pass, true phone/browser proof, dropoff/cancel completion, or delivery success.
- Objective 1 constraint: PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this O5 sprint does not close 2D LiDAR / ToF material, WAVE ROVER/UART, or HIL proof.
- Expected OKR movement: `no OKR percentage lift`.

## KR Breakdown Or Update

1. PC material follow-up gate accepts only safe `verified_terminal_result_material_review_handoff` artifacts, summaries, Robot aliases, or compatible nested diagnostics/status summaries.
2. Robot diagnostics exposes a sanitized `robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary` alias.
3. Mobile/web renders a read-only follow-up escalation status panel with safe copy and no primary action enablement.
4. All surfaces preserve `source=software_proof`, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
5. The sprint creates handoff-ready status evidence for follow-up, not verified terminal delivery/dropoff/cancel result material.

## Product Requirements

1. The PC gate must emit capability `verified_terminal_result_material_followup_escalation_status`.
2. The evidence boundary must be `software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate`.
3. Required statuses:
   - `escalated_for_terminal_result_material_followup_not_proven`
   - `waiting_for_terminal_result_material_backfill_not_proven`
   - `needs_support_owner_reassignment_not_proven`
   - `rejected_unsafe_terminal_result_followup_not_proven`
   - `blocked_missing_terminal_result_review_handoff_not_proven`
4. Follow-up output must include safe `evidence_ref`, terminal result type, source handoff status, assigned owner, support owner, reviewer route, required material backfill, escalation reason, blocked reason when present, safe copy, and fail-closed flags.
5. Inputs that are missing the prior review handoff, use unsupported schemas, contain unsafe raw artifacts, credentials, local paths, ROS/control terms, hardware raw details, success claims, or control enablement must fail closed.
6. Mobile/web copy must make clear that this is a follow-up escalation status only, not delivery success and not true phone/browser proof.
7. Robot diagnostics must remain read-only and must not expose raw terminal material, raw diagnostics fetches, ACK/cursor mutation hints, replay/resubmit hints, robot-control hints, credentials, paths, checksums, ROS topics, serial/UART details, WAVE ROVER details, hardware raw details, or reviewer-resolution claims.

## Priority And Acceptance Criteria

Priority is P0 for Objective 5 because it is the lowest Objective and this is the next concrete terminal-result material rung after review handoff.

Acceptance criteria:

- Autonomy, Robot, and Full-Stack implementation tasks are ready to launch in parallel with non-overlapping file scopes.
- The implementation can be validated through fenced commands only: `py_compile`, focused `unittest`, CLI `--help`, `node --check`, `json.tool`, `rg`, and scoped `git diff --check`.
- The output preserves `source=software_proof`, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `no OKR percentage lift`.
- The status is useful to field owner / support / reviewer without implying real O5 external proof.

## Responsible Engineers

- Autonomy Algorithm Engineer owns PC evidence gate and interface contract documentation.
- Robot Platform Engineer owns Robot diagnostics safe alias and remote diagnostics documentation.
- User Touchpoint Full-Stack Engineer owns mobile/web read-only status panel and mobile user-flow documentation.
- Product Manager / OKR Owner owns later Task D closeout after worker evidence returns.

## Risks, Blockers, And Evidence Chain Gaps

- Real verified terminal delivery/dropoff/cancel result material is still missing.
- Real O5 external proof is still missing: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, and worker/cutover are absent.
- True phone/browser proof is still missing; local mobile/web proof is not real iPhone/Android behavior.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` is still unresolved / `hardware_material_pending`; this work must not claim Objective 1 hardware closure.
- Docker/local software proof cannot prove WAVE ROVER/UART/HIL, route/elevator field pass, Nav2/fixed-route runtime pass, dropoff/cancel completion, delivery result, or delivery success.

## Sprint Documents To Create Or Update

Create now:

- `sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/pre_start.md`
- `sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/prd.md`
- `sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/tech-plan.md`

Do not create closeout files in this run. Later Task D must update `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` only after worker evidence returns.
