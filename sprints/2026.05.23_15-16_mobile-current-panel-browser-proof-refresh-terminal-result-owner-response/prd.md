# Mobile Current Panel Browser Proof Refresh Terminal Result Owner Response PRD

Run time: 2026-05-23 15:04 Asia/Shanghai

## User Value And Product North Star

User value: phone and support users need the current mobile panel to reflect the newest terminal-result owner-response states without enabling unsafe actions. When verified terminal-result material is still missing or under review, the UI should make that clear with safe summaries instead of implying delivery success.

Product north star: the mobile entrypoint should be the ordinary user's only operational surface, while support evidence remains safe, redacted, and explicit about proof boundaries. A local browser proof refresh is useful only if it makes the current panel more trustworthy and preserves `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## OKR Mapping

- Primary Objective: Objective 4, phone user experience and low-cost production boundary.
- Secondary guardrail: Objective 5, cloud/data path must not be misrepresented as progressed without real external material.
- Hardware guardrail: Objective 1 and PR #5 must not be treated as resolved while `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`.

## KR Breakdown

Objective 4 KR support:

- KR1 / KR5: phone flow remains understandable for non-technical users and support owners.
- KR7: mobile UI current-panel proof stays aligned after new terminal-result owner-response panels were added.
- KR4: remote diagnostics data shown on mobile remains redacted, safe, and support-oriented.

Objective 5 guardrail:

- No O5 KR is claimed complete in this sprint.
- O5 stays blocked on real external/terminal-result material unless new real evidence arrives under the same safe `evidence_ref`.

## Core Lever

Refresh local Chromium current-panel proof for:

- `verified_terminal_result_material_owner_response_intake`
- `verified_terminal_result_material_owner_response_review_decision`

The refresh should produce `mobile_current_panel_browser_proof_refresh_terminal_result_owner_response` and preserve `software_proof_docker_mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_gate`.

## Scope

In scope for the subsequent implementation sprint:

- Extend the current-panel browser proof command to require the terminal-result owner-response intake and review-decision panels.
- Confirm the browser proof uses a fresh local Chromium profile, captures current-panel evidence, and reports zero console errors.
- Confirm Start Delivery, Confirm Dropoff, and Cancel remain disabled for the blocked/not_proven material states.
- Confirm the panel text and safe summary show `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not true phone/browser`.
- Update `docs/product/mobile_user_flow.md` during implementation/closeout to reflect the current terminal-result owner-response browser proof boundary.
- Close the sprint with `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` updates only after implementation evidence exists.

Out of scope for this planning task:

- Product code changes.
- Test code changes.
- `OKR.md` updates.
- Non-sprint docs updates.
- Hardware configuration, WAVE ROVER, UART, launch parameters, ROS2 behavior, or cloud production changes.

## Priority And Acceptance Criteria

Priority: P0 for Objective 4 drift prevention, because the previous O4 current-panel proof predates the terminal-result owner-response intake and review-decision panels.

Acceptance criteria for the implementation sprint:

- Browser gate produces `software_proof_docker_mobile_current_panel_browser_proof_refresh_terminal_result_owner_response_gate`.
- Evidence names include `mobile_current_panel_browser_proof_refresh_terminal_result_owner_response`.
- Browser proof covers `verified_terminal_result_material_owner_response_intake` and `verified_terminal_result_material_owner_response_review_decision`.
- Current-panel proof keeps `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Final evidence says `not true phone/browser`.
- Final evidence says no OKR percentage lift unless real external/terminal-result/phone/hardware material appears.
- PR #5 state remains explicit: `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`.

## Responsible Engineers

- `full-stack-software-engineer`: implementation owner for browser gate, mobile tests, local browser evidence, and mobile product doc sync.
- `robot-software-engineer`: read-only consultation owner for diagnostics safe-summary compatibility and command safety semantics.
- `product-okr-owner`: closeout owner for evidence acceptance, sprint docs, `OKR.md`, and progress log after implementation.

## Evidence Chain Needed

- Local fresh-profile Chromium/browser gate logs and artifact directory under this sprint.
- Unit tests for `mobile/web` entrypoint and any compatibility wrapper already used in the repo.
- `rg` evidence showing capability name, evidence boundary, panel names, fail-closed flags, PR #5 unresolved thread, `not true phone/browser`, and no OKR percentage lift.
- Scoped `git diff --check`.

## Risks, Blockers, And Missing Evidence

- Real O5 progress remains blocked by missing public ingress/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, and real terminal-result material.
- Real phone proof remains blocked by missing iPhone/Android device behavior, production app evidence, and real PWA prompt/userChoice.
- Hardware progress remains blocked by missing 2D LiDAR / ToF source/receipt/procurement/installation/wiring/power/calibration/HIL-entry material and PR #5 thread `PRRT_kwDOSWB9286CJ3tX`.
- Route/elevator progress remains blocked by missing real route/elevator field pass, Nav2/fixed-route runtime evidence, dropoff/cancel completion, delivery result, and delivery success.
