# Verified Terminal Result Material Owner Response Reviewer ACK Review Decision Pre-start

Run time: 2026-05-24 00:01 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Trigger

CEO request: open the next fresh Epic sprint for `verified_terminal_result_material_owner_response_reviewer_ack_review_decision` after `verified_terminal_result_material_owner_response_reviewer_ack_intake`.

This sprint is planned as function-forward work, not broad test expansion. The implementation phase should deliver PC gate + Robot safe alias + mobile read-only panel + docs/OKR closeout, with tests kept as narrow fences.

## Read Evidence

- `AGENTS.md`: Epic sprint planning must create `pre_start.md`, `prd.md`, and `tech-plan.md`; implementation, tests, and fixes must be handled by role-specific engineer subagents, while Product owns sprint record, acceptance boundary, and OKR closeout.
- `OKR.md` 4.1: Objective 5 is still the lowest at about 68%; Objective 1 is about 81%; Objective 2/3/4 are about 99%.
- Latest sprint `sprints/2026.05.23_23-24_verified-terminal-result-material-owner-response-reviewer-ack-intake/final.md`: completed `verified_terminal_result_material_owner_response_reviewer_ack_intake` as `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate`; no OKR percentage lift.
- GitHub PR #5 thread state supplied for planning: `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved; `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`.
- `docs/vendor/VENDOR_INDEX.md`: local vendor references are the source boundary for Orange Pi, WAVE ROVER, UART JSON, and hardware assumptions; they do not prove real 2D LiDAR / ToF procurement, installation, wiring, power, calibration, HIL-entry, WAVE ROVER powered bench, UART/HIL logs, or reviewer resolution.
- `docs/product/mobile_user_flow.md`: mobile panels in this family must stay read-only, consume Robot safe summaries, keep Start Delivery / Confirm Dropoff / Cancel disabled, and not infer delivery success from software-proof metadata.
- `docs/product/cloud_4g_infrastructure.md`: cloud/phone/ACK evidence remains Docker/local software proof unless real public HTTPS/TLS, 4G/SIM, OSS/CDN, production DB/queue, worker/cutover, or external probe evidence is supplied.

## Product North Star

The product north star remains a phone-friendly ROS2 trash-delivery robot whose cloud/support evidence chain is safe enough for ordinary users and support teams. Reviewer ACK review-decision metadata can guide next material routing, but it must not become robot control, delivery success, true phone proof, real cloud proof, HIL, or PR #5 resolution.

## User Value

This sprint lets support, owner, and reviewer convert a sanitized reviewer ACK intake into an explicit review decision: accepted for next handoff, missing material, reassignment required, unsafe/rejected, blocked by source gap, or evidence-ref mismatch. The user value is clearer next action under the same safe `evidence_ref`, while ordinary phone users remain protected from unsafe primary actions.

## Scope Boundary

Target capabilities:

- `verified_terminal_result_material_owner_response_reviewer_ack_review_decision`
- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary`
- `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_gate`

Required false-state flags:

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

This sprint must not claim PR #5 resolved, HIL, true phone/browser proof, real terminal result, real delivery/dropoff/cancel result, real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, WAVE ROVER/UART proof, LiDAR/ToF installed proof, route/elevator field pass, field pass, or delivery success.

## Owners

- Product Manager / OKR Owner: this planning chain, later `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md`.
- User Touchpoint Full-Stack Engineer: PC gate and mobile read-only panel.
- Robot Platform Engineer: Robot diagnostics safe alias and API/status consumption boundary.

## Blocker History Check

The latest sprint moved the ladder from owner-response review handoff to reviewer ACK intake and explicitly kept missing-material and Docker-only proof boundaries. This sprint continues the same ladder into reviewer ACK review decision instead of consuming the same blocker as a generic wrapper.

The root blockers remain unchanged: real external O5 proof, verified terminal delivery/dropoff/cancel result materials, true phone/browser proof, PR #5 real 2D LiDAR / ToF materials, WAVE ROVER/UART/HIL evidence, route/elevator field proof, operator report, and reviewer resolution are absent on this Docker-only host.

## Sprint Documents

This fresh Epic sprint starts with:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Implementation closeout must later add:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
