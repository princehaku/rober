# Mobile Current Panel Browser Proof Refresh Field Evidence Followup PRD

Run time: 2026-05-23 19:20 Asia/Shanghai

## Product North Star

Rober should feel like a dependable phone-first trash delivery robot, even when the current environment only supports local software proof. The product standard is that a user or operator can read the phone-facing state and know what is safe, blocked, missing, and not proven without interpreting raw ROS2, hardware, cloud, or field-material internals.

## User Value

The immediate user is the operator or reviewer checking whether the latest field-evidence follow-up panel still appears in the current mobile panel browser proof. They need proof that the newest `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status` mobile panel is covered by the local browser gate while all primary actions remain disabled.

For ordinary phone users, the value is conservative clarity: the page can explain that field-evidence follow-up is still missing real materials, but it must not imply route/elevator field pass, Objective 5 external proof, true phone/browser acceptance, HIL, or delivery success.

## OKR Mapping

- Objective 5 is still the lowest Objective at about 68%. This sprint does not directly target Objective 5 because the missing proof requires real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, verified terminal result, and true phone/browser evidence.
- Objective 4 is the fallback target: refresh current-panel local browser proof for the latest mobile panel while preserving phone-safe fail-closed controls.
- Objective 1 remains about 81%; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`.
- Objective 2 and Objective 3 remain about 99%; this sprint does not prove route/elevator field pass, Nav2/fixed-route runtime, task record, dropoff/cancel completion, verified terminal result, or delivery result.

## KR Breakdown Or Update

KR-A Full-Stack implementation and validation:
Refresh `phone_browser_acceptance_gate.py` current-panel/browser proof so it can stamp the latest field-evidence follow-up panel with `software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate` and assert the required fail-closed flags.

KR-B Robot safety consultation:
Confirm, read-only, that the Robot diagnostics summary consumed by the mobile panel stays safe for browser proof and does not expose control, raw diagnostics, hardware, credential, or success semantics.

KR-C Product closeout after A/B:
After implementation and Robot consultation, update closeout docs only if the evidence is present. Preserve no OKR percentage lift and state the proof boundary accurately.

## Core Grab

The sprint should reuse the existing current-panel browser proof machinery instead of adding a new browser-proof script. The capability is a proof refresh for the latest mobile panel, not a new product success claim.

Required strings and flags:

- `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`
- `software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- no OKR percentage lift

## Needs To Be Done

- Task A Full-Stack: implement and validate the local current-panel browser proof refresh against the latest field-evidence follow-up mobile panel.
- Task B Robot: review the summary and panel data boundary read-only, ensuring Robot-safe metadata remains safe for browser proof and control-disabled display.
- Task C Product: after Task A and Task B, update `tech-done.md`, `side2side_check.md`, `final.md`, and any required docs/OKR progress only if allowed by the next implementation sprint scope.

## Priority And Acceptance

Priority:

1. Preserve safety and evidence language.
2. Cover the latest field-evidence follow-up panel in local browser proof.
3. Keep implementation fenced to Full-Stack files, with Robot read-only consultation.
4. Close out with no OKR percentage lift unless real evidence appears.

Acceptance criteria for implementation:

- Browser proof output includes `software_proof_docker_mobile_current_panel_browser_proof_refresh_field_evidence_followup_gate`.
- The proof explicitly covers `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- Output and docs preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- The implementation does not claim true phone/browser proof, Objective 5 external proof, route/elevator field pass, HIL, PR #5 resolution, verified terminal result, or delivery success.

Acceptance criteria for this planning phase:

- `pre_start.md`, `prd.md`, and `tech-plan.md` exist in the new sprint folder.
- `tech-plan.md` contains `## OKR 最低优先级核对`.
- Planning docs name Objective 5, Objective 4, `PRRT_kwDOSWB9286CJ3tX`, the capability, the evidence boundary, and all fail-closed flags.

## Responsible Engineers

- Task A: User Touchpoint Full-Stack Engineer.
- Task B: Robot Platform Engineer, read-only safety boundary consultation.
- Task C: Product Manager / OKR Owner after A/B.

## Risks, Blockers, And Evidence Chain

- Real Objective 5 proof is blocked by missing external cloud, terminal-result, and true phone/browser materials.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` is still blocked by missing real 2D LiDAR / ToF materials and HIL-entry evidence.
- A local browser proof refresh is useful only as `software_proof`; it is not a real phone/browser pass.
- The next implementation must not introduce any route, upload, action, ACK, cursor, diagnostics fetch, procurement, GitHub, or robot command capability from this panel proof.

## Sprint Documents

Created in this planning phase:

- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/pre_start.md`
- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/prd.md`
- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/tech-plan.md`

To create or update after implementation:

- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/tech-done.md`
- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/side2side_check.md`
- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/final.md`
- Relevant `docs/` entries only if the implementation changes product behavior or proof contract.
