# Verified Terminal Result Material Owner Response Reviewer ACK Intake PRD

Run time: 2026-05-23 23:04 Asia/Shanghai

## Problem

`verified_terminal_result_material_owner_response_review_handoff` packages the owner/support/reviewer route, but the next workflow gap is reviewer ACK intake. Support and field owners need to know whether the reviewer has acknowledged the handoff, found missing materials, requested reassignment, or rejected unsafe ACK content. Without this rung, the project can show a handoff packet but cannot safely record the reviewer's first response state.

The host still has Docker/local proof only. Therefore this sprint must improve workflow clarity without upgrading proof status or changing OKR percentages.

## User Value And Product North Star

User value: support, field owner, and reviewer get a clear safe intake record for reviewer ACK status, missing evidence, reassignment needs, and unsafe ACK rejection under the same safe evidence chain.

Product north star: a low-cost ROS2 trash-delivery robot whose phone/cloud evidence flow is explainable, conservative, and impossible to confuse with delivery success until real field, cloud, hardware, and phone evidence exists.

## OKR Mapping

- Primary: Objective 5, about 68%, currently lowest. This sprint targets the cloud/phone terminal-result evidence workflow, but no OKR percentage lift is expected because it remains Docker/local software proof.
- Secondary: Objective 4. `mobile/web` must render the reviewer ACK intake as read-only and keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Secondary: Objective 1. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; reviewer ACK intake must preserve that hardware-material pending state and not imply HIL or reviewer resolution.

## KR Breakdown

- KR-A: PC-only gate creates `verified_terminal_result_material_owner_response_reviewer_ack_intake` from safe owner-response review-handoff metadata and records accepted/missing/reassignment/unsafe ACK states.
- KR-B: Robot diagnostics exposes `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary` as a read-only safe alias with sanitized copy and required false-state flags.
- KR-C: `mobile/web` renders a read-only reviewer ACK intake panel from the Robot alias or compatible safe summary, while primary actions remain disabled.
- KR-D: Interface and product docs describe schema, safe fields, forbidden fields, evidence boundary, and remaining proof gaps.

## Core Lever

The core lever is converting owner/support/reviewer handoff into a reviewer ACK intake record. This is workflow progress for Objective 5 evidence handling, not a new claim about robot delivery or production cloud readiness.

## Requirements

The reviewer ACK intake summary must include only safe fields such as:

- capability: `verified_terminal_result_material_owner_response_reviewer_ack_intake`
- schema/version for the intake summary
- safe `evidence_ref`
- safe `command_id` when present
- source handoff status
- terminal result type
- reviewer ACK status, for example acknowledged, missing material, reassignment needed, rejected unsafe ACK, or blocked missing handoff
- owner/support/reviewer route
- missing or rejected material list
- next required evidence
- blocker reason when present
- backend-provided safe copy
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

The intake must fail closed when required safe IDs are missing, evidence refs conflict, source handoff is absent, unsafe text appears, raw paths or credentials appear, success wording appears, or any true-state control flag is true.

## Non-goals

This sprint must not write product code during planning, implement robot motion, upload materials, perform GitHub review actions, close PR #5, enable Start Delivery, Confirm Dropoff, or Cancel, mutate ACK/cursors, replay/resubmit commands, run real hardware, or claim production cloud proof.

It must not claim PR #5 resolved, HIL, true phone/browser proof, real terminal result, real delivery/dropoff/cancel result, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, WAVE ROVER/UART proof, route/elevator field pass, or delivery success.

## Priority And Acceptance

P0:

- PC gate creates and validates reviewer ACK intake from safe handoff metadata.
- Robot diagnostics alias exposes the same safe summary without unsafe fields.
- Mobile read-only panel renders the reviewer ACK intake and keeps `primary_actions_enabled=false`.
- Required evidence strings appear in docs and focused tests.

P1:

- Safe copy is Chinese-first and explains the support/field-owner/reviewer next step.
- Fixtures cover acknowledged, missing material, reassignment needed, unsafe ACK, and missing source handoff.

Acceptance boundary:

- All worker checks stay fenced to touched areas.
- No broad regression sweep is required.
- Closeout must keep no OKR percentage lift unless real external or terminal-result materials unexpectedly arrive.

## Responsible Engineers

- User Touchpoint Full-Stack Engineer: Task A PC gate, focused PC tests, PC README/interface docs, Task C mobile panel, fixture, and mobile tests.
- Robot Platform Engineer: Task B diagnostics alias, focused diagnostics tests, operator-gateway diagnostics docs, and remote 4G product docs.
- Product Manager / OKR Owner: closeout docs, `OKR.md`, and `docs/process/okr_progress_log.md` after implementation.

## Risks And Missing Evidence

- Objective 5 still lacks real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, and verified terminal delivery/dropoff/cancel result.
- Objective 1 still lacks PR #5 hardware materials for thread `PRRT_kwDOSWB9286CJ3tX`, including real 2D LiDAR / ToF SKU/source/receipt, installation, wiring, power, calibration, HIL-entry, WAVE ROVER/UART proof, and reviewer resolution.
- Objective 2/3/4 still lack route/elevator field pass, Nav2/fixed-route runtime proof, real task record, dropoff/cancel completion, delivery result, and true mobile-device evidence.
- Current host can only prove Docker/local software behavior.

## Sprint Documents To Update Later

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
