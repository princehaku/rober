# Mobile Current Panel Browser Proof Refresh Field Evidence Followup Pre Start

Run time: 2026-05-23 19:20 Asia/Shanghai

## Sprint Type

sprint_type: epic

## User Value And North Star

Rober's product north star is still a low-cost, phone-first trash delivery robot whose users can understand readiness without touching ROS2, SSH, serial tools, or hardware debug flows.

This sprint creates the planning boundary for a latest panel browser proof refresh: `phone_browser_acceptance_gate.py` should cover the newest `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status` mobile panel in local browser proof, while preserving the fail-closed mobile experience. The user value is confidence that the current phone-facing panel set is still visible, current, and safe after the field-evidence follow-up additions.

## Background Evidence

- `OKR.md` 4.1 says Objective 5 is currently lowest at about 68%; Objective 1 is about 81%; Objective 2, Objective 3, and Objective 4 are about 99%.
- Latest completed sprint `sprints/2026.05.23_18-19_field-evidence-rerun-acceptance-owner-response-reviewer-ack-followup-escalation-status/final.md` added `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status` across PC, Robot, and mobile local software proof.
- That latest sprint explicitly did not prove true phone/browser behavior, Objective 5 external proof, route/elevator field pass, HIL, verified terminal result, dropoff/cancel completion, or delivery success.
- Live PR #5 evidence remains: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, and `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`.
- Current host has no real hardware and only Docker/local proof. This sprint must not add another Objective 5 or PR #5 real-material blocker wrapper and must record no OKR percentage lift.

## OKR Mapping

- Objective 5 remains the lowest priority by percentage, but the missing proof is external and real-material bound: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, verified terminal result, and true phone/browser evidence.
- Objective 4 is the actionable fallback for this sprint: refresh local current-panel browser proof so the latest field-evidence follow-up mobile panel is included in the proof surface.
- Objective 1 remains blocked by PR #5 `PRRT_kwDOSWB9286CJ3tX` hardware material pending evidence and must not be represented as improved by this sprint.
- Objective 2 and Objective 3 remain dependent on real route/elevator field materials and delivery/result evidence; this sprint only keeps their phone-facing follow-up panel safely visible.

## Core Grab

Use the existing `phone_browser_acceptance_gate.py` current-panel browser proof path instead of inventing a new proof class. The planned proof boundary is:

`software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate`

The proof must keep:

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- no OKR percentage lift

## Scope Boundary

In scope for this planning sprint:

- Create the Epic planning chain starter documents for the new sprint.
- Define Task A Full-Stack implementation and validation ownership.
- Define Task B Robot read-only safety boundary consultation.
- Define Task C Product closeout after A/B.
- Define files, proof strings, and acceptance commands for the next implementation phase.

Out of scope for this planning sprint:

- Product code changes.
- Test code changes.
- `OKR.md` changes.
- `tech-done.md`, `side2side_check.md`, or `final.md` closeout.
- Real phone/browser, real Objective 5 external proof, real route/elevator field pass, HIL, or delivery success claims.

## Risks And Blockers

- Objective 5 cannot be lifted without real external proof and terminal-result materials.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` cannot be resolved without real 2D LiDAR / ToF SKU, source, receipt, procurement, installation, wiring, power, calibration, and HIL-entry materials.
- A local Chromium-family browser proof is not a true iPhone/Android device proof.
- The next implementation must avoid enabling Start Delivery, Confirm Dropoff, or Cancel through a panel proof refresh.

## Sprint Documents To Create Or Update

- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/pre_start.md`
- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/prd.md`
- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/tech-plan.md`
