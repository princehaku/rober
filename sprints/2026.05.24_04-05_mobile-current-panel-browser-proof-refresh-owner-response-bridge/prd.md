# Mobile Current Panel Browser Proof Refresh Owner Response Bridge PRD

Run time: 2026-05-24 04:03 Asia/Shanghai

## Sprint Type

sprint_type: epic

## User Value And Product North Star

The user value is clarity without unsafe action: a phone user, support reviewer, or field owner should see the latest owner-response bridge state on the mobile surface and know that it is still blocked on real materials, not safe to control, and not delivery success.

The product north star remains a low-cost phone-first trash delivery robot. The phone surface must be understandable to ordinary users, but it must not hide safety blockers or convert local software proof into real phone/browser, robot, cloud, or delivery proof.

## Problem

The latest field-evidence rerun owner-response bridge is visible in local software surfaces, but the current-panel browser proof needs to be refreshed so `phone_browser_acceptance_gate.py` covers the latest mobile panel:

`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge`

Without this refresh, the mobile/browser proof can lag behind the latest read-only panel. With the refresh, support can verify the newest panel is visible and fail-closed in local Chromium-family proof while still preserving `not true phone/browser proof`.

## Non Goals

- Do not create a new O5 / PR #5 / route material metadata wrapper.
- Do not claim Objective 5 external proof.
- Do not claim PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved.
- Do not claim hardware, WAVE ROVER, UART, HIL, 2D LiDAR/ToF, route/elevator field pass, Nav2/fixed-route runtime, verified terminal result, dropoff/cancel completion, delivery result, or delivery success.
- Do not enable Start Delivery, Confirm Dropoff, Cancel, ACK, cursor fetch, material upload, review action, owner-response action, GitHub mutation, procurement action, raw diagnostics fetch, replay, resubmit, or robot command paths.
- Do not modify code in this planning-only phase.

## OKR Mapping

- Objective 5: still lowest at about 68%, but blocked on real external/cloud/terminal-result materials. This PRD explicitly avoids another O5 local-only wrapper and records no OKR percentage lift.
- Objective 4: fallback objective for this sprint. The value is current mobile panel browser proof coverage for the latest safe owner-response bridge panel.
- Objective 1: not advanced; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains `hardware_material_pending`.
- Objective 2 / Objective 3: not advanced; no route/elevator field pass, task record, Nav2/fixed-route runtime, terminal result, dropoff/cancel completion, or delivery result is produced.

## KR Breakdown

- O4 KR7: mobile UI remains current, readable, and fail-closed for the latest owner-response bridge state.
- O4 KR4: remote diagnostics/support material remains phone-safe and read-only.
- O5 KR1/KR6: blocked, explicitly not advanced.
- O1 KR1-KR5: blocked, explicitly not advanced.

## Product Requirements

1. The browser proof refresh must stamp the evidence as:

   `software_proof_docker_mobile_current_panel_browser_proof_refresh_owner_response_bridge_gate`

2. The proof must cover:

   `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge`

3. The mobile panel must remain read-only and fail-closed.
4. The panel must keep Start Delivery, Confirm Dropoff, and Cancel disabled.
5. The panel must visibly preserve:

   - `not_proven`
   - `delivery_success=false`
   - `primary_actions_enabled=false`
   - `safe_to_control=false`
   - no OKR percentage lift
   - not true phone/browser proof

6. The panel must explain that next real progress requires owner-provided real materials under the same safe `evidence_ref`.
7. The panel must not expose raw JSON, raw artifacts, ROS topics, `/cmd_vel`, serial/UART paths, WAVE ROVER details, credentials, local filesystem paths, checksums, complete artifacts, raw diagnostics, ACK/cursor routes, review routes, owner-response routes, material routes, GitHub mutation, procurement action, replay/resubmit controls, or robot commands.

## Acceptance Criteria

Task A Full-Stack acceptance:

- `phone_browser_acceptance_gate.py` can validate the owner-response bridge panel under the new boundary.
- Fresh local proof remains local Chromium-family software proof only.
- Existing fail-closed command gating remains unchanged.
- Focused mobile tests and browser proof commands pass.

Task B Robot acceptance:

- Robot Platform confirms read-only safety boundary with no Robot code change unless a missing safe field is discovered.
- Robot consultation confirms no raw ROS, `/cmd_vel`, serial/UART, WAVE ROVER, credential, local path, checksum, complete artifact, or control/success field is needed.

Task C Product acceptance:

- Closeout states Objective 5 remains lowest and blocked on real external/terminal-result materials.
- Closeout states Objective 4 receives only local browser-proof coverage refresh, no true phone/browser proof.
- Closeout states PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live review evidence changes.
- Closeout preserves no OKR percentage lift.

## Responsible Engineer Mapping

- User Touchpoint Full-Stack Engineer: implementation, mobile fixture/test update, `phone_browser_acceptance_gate.py` coverage, local browser proof artifact generation.
- Robot Platform Engineer: read-only safety consultation and proof-boundary confirmation.
- Product Manager / OKR Owner: closeout docs and OKR truth boundary after A/B evidence.

## Risks And Evidence Gaps

- Browser proof can pass locally while still not being true iPhone/Android browser proof.
- The panel can be current while the actual field owner material remains missing.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` can remain unresolved even after this sprint.
- Objective 5 can remain the lowest objective because this sprint does not produce public ingress, 4G/SIM, OSS/CDN, production DB/queue, worker/cutover, or verified terminal-result evidence.
- Any implementation that enables primary actions, implies delivery success, or hides `hardware_material_pending` fails the PRD.

## Sprint Documents

This planning-only task creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Later implementation must create:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
