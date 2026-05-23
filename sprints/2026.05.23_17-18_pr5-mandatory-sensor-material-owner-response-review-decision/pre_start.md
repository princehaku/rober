# PR #5 Mandatory Sensor Material Owner Response Review Decision - Pre Start

## Sprint Metadata

- sprint_type: epic
- Sprint path: `sprints/2026.05.23_17-18_pr5-mandatory-sensor-material-owner-response-review-decision/`
- Capability: `pr5_mandatory_sensor_material_owner_response_review_decision`
- Evidence boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate`
- Start time: 2026-05-23 17:00 Asia/Shanghai
- Product owner: `product-okr-owner`
- Engineering owners: `hardware-engineer`, `robot-software-engineer`, `full-stack-software-engineer`

## User Value And Product North Star

User value: reviewers and field owners need one safe decision state after PR #5 material owner-response intake, so they can tell whether the response is ready for reviewer closeout, needs more material, is unsafe, or is blocked before anyone claims hardware proof.

Product north star: `rober` remains a phone-friendly, low-cost ROS2 trash delivery robot whose product status separates local software proof from real 2D LiDAR / ToF material, WAVE ROVER/UART/HIL, true phone/browser evidence, O5 external cloud proof, and delivery success.

## OKR Mapping

- Objective 5 remains the lowest objective at about 68%, but the current Docker-only host lacks public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, real phone/browser, and verified terminal result material. This sprint must not add another O5 local metadata-only layer.
- Objective 1 is about 81% and has live PR #5 review evidence: thread `PRRT_kwDOSWB9286CJ3tX` is still unresolved / `is_resolved=false` / `is_outdated=false` / `resolved_by=null` on `docs/product/production_hardware_boundary.md`, with `hardware_material_pending`.
- This sprint advances the O1 PR #5 material chain by turning safe owner-response intake metadata into a review-decision state. It does not increase OKR percentage unless real 2D LiDAR / ToF material or reviewer resolution appears in a later sprint.

## Previous Sprint Input

Previous sprint: `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/`.

Accepted boundary from previous sprint:

- Capability: `pr5_mandatory_sensor_material_owner_response_intake`.
- Gate: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate`.
- Safe states: `accepted`, `missing`, `rejected`, `unsafe`, `blocked`.
- Non-claims: no PR #5 resolution, no real 2D LiDAR / ToF, no WAVE ROVER/UART/HIL, no O5 external proof, no true phone/browser proof, no route/elevator pass, no delivery success.

This sprint consumes that intake output and creates the next review-decision rung only.

## Recent Blocker Scan

Scanned the latest two sprint finals before this kickoff:

- `sprints/2026.05.23_16-17_pr5-mandatory-sensor-material-owner-response-intake/final.md`: closed as owner-response intake software proof; blocker remains PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved and real 2D LiDAR / ToF material pending.
- `sprints/2026.05.23_15-16_mobile-current-panel-browser-proof-refresh-terminal-result-owner-response/final.md`: closed as local browser/current-panel proof; blocker remains real O5 external proof, real terminal result, true phone/browser, HIL, and PR #5 material unresolved.

Decision: this is not a third sprint consuming the same blocker as a generic blocked closeout. It is the explicit next rung after `pr5_mandatory_sensor_material_owner_response_intake`: `pr5_mandatory_sensor_material_owner_response_review_decision`. The sprint must convert safe intake metadata into bounded review-decision states and preserve `not_proven`.

## Core Lever

Create a fail-closed review-decision path across four scopes:

- Hardware PC gate: classify owner-response intake into review decisions.
- Robot diagnostics safe alias: expose only sanitized review-decision summary fields.
- Full-Stack mobile read-only panel: display the decision without enabling actions.
- Product closeout: verify evidence boundaries and update sprint closeout documents after implementation.

## Safe Review Decisions

Allowed review-decision states:

- `accepted_for_reviewer_closeout_not_proven`
- `needs_more_material_not_proven`
- `rejected_unsafe_material_not_proven`
- `blocked_missing_owner_response_intake_not_proven`
- `blocked_evidence_ref_mismatch_not_proven`

Required conservative flags:

- `software_proof`
- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `docs/vendor/VENDOR_INDEX.md`

## Scope Boundary

In scope:

- Create planning docs for this fresh Epic sprint.
- Define owner/file scopes and acceptance commands.
- Preserve the PR #5 unresolved state and the Docker-only proof boundary.

Out of scope:

- Product code changes during planning.
- `OKR.md` edits during planning.
- `docs/process/okr_progress_log.md` edits during planning.
- PR #5 thread resolution.
- Any claim of real hardware, HIL, true phone/browser, O5 external proof, route/elevator field pass, or delivery success.

## Required Sprint Documents

Planning phase creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Implementation/closeout phase must later create:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
