# Verified Terminal Result Material Owner Response Review Handoff PRD

Run time: 2026-05-23 22:02 Asia/Shanghai

## Problem

`verified_terminal_result_material_owner_response_review_decision` already tells the project whether owner-response material is acceptable for next review movement, still missing, rejected, unsafe, evidence-ref mismatched, or blocked. The next product gap is handoff: support, owner, and reviewer need one safe packet that carries that decision into the next owner/support/reviewer workflow without implying the robot delivered anything.

The repo must keep moving on the lowest Objective, Objective 5, while respecting the local-only environment. This sprint is not a new cloud command wrapper; it is a handoff rung for verified terminal-result material review metadata.

## User Value And Product North Star

User value: support and field owners get a clear next-action packet for verified terminal-result material, including safe IDs, owner/support/reviewer routing, missing evidence, and copyable handoff text, while phone users remain protected from unsafe or misleading control states.

Product north star: a low-cost ROS2 trash-delivery robot whose phone/cloud evidence chain is safe, explainable, and impossible to confuse with real delivery success until real field/cloud/hardware proof exists.

## OKR Mapping

- Primary: Objective 5, about 68%, currently lowest. This handoff improves the cloud/phone evidence workflow around terminal-result review materials, but should not lift the OKR percentage without real external proof or verified terminal result materials.
- Secondary: Objective 4, because `mobile/web` must render the handoff read-only and keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Secondary: Objective 1, because PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; the handoff must preserve that unresolved material state and not imply hardware proof.

## KR Breakdown

- KR-A: PC-only evidence gate can convert `verified_terminal_result_material_owner_response_review_decision` safe metadata into `verified_terminal_result_material_owner_response_review_handoff` with `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- KR-B: Robot diagnostics exposes a safe alias for the same handoff summary without raw diagnostics, control routes, ACK/cursor mutation, material upload, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, local paths, complete artifacts, checksums, or success wording.
- KR-C: `mobile/web` renders a read-only handoff panel from the Robot diagnostics alias or compatible safe summary, keeps all primary actions disabled, and never fetches raw materials or infers true phone/browser proof.
- KR-D: docs explain the interface, product flow, evidence boundary, owner/support/reviewer route, and remaining real-material gaps.

## Core Lever

Turn a review decision into a reviewer-ready handoff packet. The core product lever is not more testing volume; it is a small, fenced evidence workflow that makes the next real-material request unambiguous and keeps unsafe action states closed.

## Requirements

The handoff summary must include only safe fields such as:

- capability: `verified_terminal_result_material_owner_response_review_handoff`
- schema/version for the handoff summary
- safe `evidence_ref`
- safe `command_id` when present
- source review decision status
- terminal result type
- owner/support/reviewer routing
- decision reasons
- missing or rejected material list
- next required evidence
- blocker reason when present
- backend-provided safe copy
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

The handoff must fail closed when required safe IDs are missing, `evidence_ref` conflicts, unsafe copy appears, raw paths or credentials appear, success wording appears, or any true-state control flag is true.

## Non-goals

This sprint must not implement robot motion, replay/resubmit commands, post ACKs, mutate cursors, upload materials, perform GitHub review actions, change PR #5 state, enable Start Delivery, Confirm Dropoff, or Cancel, run real hardware, or claim real external cloud proof.

It must not claim real terminal result, O5 external proof, true phone/browser proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, route/elevator field pass, HIL, WAVE ROVER/UART proof, PR #5 resolved, or delivery success.

## Priority And Acceptance

P0:

- PC gate creates and validates the handoff summary from safe review-decision metadata.
- Robot diagnostics safe alias exposes the handoff without unsafe fields.
- Mobile/web read-only panel renders the handoff and keeps `primary_actions_enabled=false`.
- Required evidence strings are present in docs and tests.

P1:

- Safe copy explains owner/support/reviewer next steps in Chinese-first product language.
- Fixture coverage includes accepted, missing/backfill, and unsafe fail-closed cases.

Acceptance boundary:

- All worker checks are fenced to touched areas.
- No broad test expansion is required.
- Closeout keeps no OKR percentage lift unless real materials unexpectedly arrive.

## Responsible Engineers

- User Touchpoint Full-Stack Engineer: PC-only gate, focused tests, README/interface docs, mobile/web panel, fixture, and mobile tests.
- Robot Platform Engineer: Robot diagnostics safe alias, focused diagnostics tests, `operator_gateway_diagnostics.md`, and `remote_4g_mvp.md`.
- Product Manager / OKR Owner: closeout docs, `OKR.md`, and `docs/process/okr_progress_log.md` after implementation.

## Risks And Missing Evidence

- Objective 5 still lacks real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, and verified terminal delivery/dropoff/cancel result.
- Objective 1 still lacks PR #5 hardware materials for thread `PRRT_kwDOSWB9286CJ3tX`, including 2D LiDAR / ToF SKU/source/receipt, installation, wiring, power, calibration, HIL-entry, WAVE ROVER/UART proof, and reviewer resolution.
- Objective 2/3/4 still lack route/elevator field pass, Nav2/fixed-route runtime proof, real task record, dropoff/cancel completion, delivery result, and true mobile-device evidence.
- Current host can only prove Docker/local software behavior.

## Sprint Documents To Update Later

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

