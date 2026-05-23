# PR #5 Mandatory Sensor Material Owner Response Review Decision - PRD

## User Value

The reviewer needs a safe, explicit decision after PR #5 mandatory sensor material owner-response intake. Without this rung, the repo can collect owner-response metadata but cannot clearly say whether the material is acceptable for reviewer closeout, still missing, unsafe, blocked by missing intake, or mismatched by `evidence_ref`.

The user-facing value is clarity without overclaiming: a support owner can see the next required material for `PRRT_kwDOSWB9286CJ3tX` while Start Delivery, Confirm Dropoff, Cancel, robot control, and delivery success remain disabled.

## Product North Star

`rober` should be a low-cost ROS2 trash delivery robot that ordinary phone users can trust. Trust here means status is honest: local Docker software proof remains separate from real 2D LiDAR / ToF source/procurement/install/calibration/HIL material, WAVE ROVER/UART/HIL proof, true phone/browser proof, O5 external cloud proof, and delivery success.

## Problem

Objective 5 is still lowest at about 68%, but the current host cannot produce the external materials needed for real O5 progress. The next actionable live review evidence is Objective 1 PR #5 thread `PRRT_kwDOSWB9286CJ3tX`, which remains unresolved on `docs/product/production_hardware_boundary.md` because mandatory sensor assumptions still need `docs/vendor/` source attribution and real 2D LiDAR / ToF material.

The previous sprint created `pr5_mandatory_sensor_material_owner_response_intake`. This sprint must not restart the same intake or create another generic blocker display. It must turn safe intake metadata into review-decision output.

## OKR Mapping

Objective 1:

- KR impact: supports the hardware boundary and sensor-material review chain for PR #5 by keeping mandatory sensor assumptions source-attributed and fail-closed.
- Current progress: about 81%.
- Expected percentage change: none during this software-proof review-decision sprint.

Objective 5:

- Current progress: about 68%, still lowest.
- Reason not targeted: no public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, real phone/browser, or verified terminal result material exists on this Docker-only host.
- Guardrail: no O5 external proof claim.

Objective 4:

- Impact: mobile read-only status clarity only.
- Guardrail: not true phone/browser proof, not production app/device proof, and `primary_actions_enabled=false`.

Objectives 2 and 3:

- Impact: none.
- Guardrail: no route/elevator field pass, Nav2/fixed-route runtime pass, terminal result, dropoff/cancel completion, or delivery success.

## KR Breakdown

KR-A Hardware PC gate:

- Input: sanitized `pr5_mandatory_sensor_material_owner_response_intake` artifact or summary.
- Output: `pr5_mandatory_sensor_material_owner_response_review_decision` artifact and summary.
- Decisions: `accepted_for_reviewer_closeout_not_proven`, `needs_more_material_not_proven`, `rejected_unsafe_material_not_proven`, `blocked_missing_owner_response_intake_not_proven`, `blocked_evidence_ref_mismatch_not_proven`.
- Source boundary: `docs/vendor/VENDOR_INDEX.md` is the required hardware source entrypoint; local vendor references do not prove real 2D LiDAR / ToF procurement, install, wiring, power, calibration, or HIL.

KR-B Robot diagnostics safe alias:

- Expose `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary`.
- Consume only safe summary fields.
- Preserve `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `hardware_material_pending`, and `not_proven`.

KR-C Full-Stack mobile read-only panel:

- Show safe review decision and next required evidence.
- Do not expose raw owner-response material, raw artifacts, credentials, serial/UART details, `/cmd_vel`, ROS topics, local paths, checksums, HIL/pass claims, PR-resolution claims, or delivery-success claims.
- Keep primary actions disabled.

KR-D Product closeout:

- Re-check sprint evidence and live PR #5 state before final.
- Record that this is `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate`.
- Preserve no OKR percentage lift unless real material appears.

## Acceptance Criteria

The sprint is accepted only if:

- The review-decision gate handles accepted, missing, unsafe/rejected, missing-intake, and evidence-ref mismatch cases.
- Robot diagnostics exposes only safe metadata and keeps conservative flags false.
- Mobile/web displays the decision read-only and keeps primary actions disabled.
- All touched product docs under `docs/` are synchronized by implementation owners.
- Technical code comments added by engineers are Chinese and explain why raw hardware/material content stays out of runtime surfaces.
- Required owner validations and scoped `git diff --check` pass.

The sprint is rejected if any output claims:

- real 2D LiDAR / ToF source/procurement/install/wiring/power/calibration/HIL proof;
- WAVE ROVER/UART/HIL proof;
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved;
- true phone/browser proof;
- O5 public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover;
- route/elevator field pass, Nav2/fixed-route runtime pass, terminal result, dropoff/cancel completion, or delivery success.

## Priority And Owner Routing

Priority: high within Docker-only constraints, because it is the next review rung after intake and is tied to live PR #5 unresolved evidence.

Responsible owners:

- Hardware Infra Engineer: PC gate and hardware/source-boundary docs.
- Robot Platform Engineer: diagnostics safe alias and runtime contract docs.
- User Touchpoint Full-Stack Engineer: mobile read-only panel and mobile flow docs.
- Product Manager / OKR Owner: closeout documents, OKR boundary review, final acceptance wording.

## Risks And Evidence Gaps

- Real 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry material is still missing.
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved until reviewer action or real material closeout.
- O5 external proof remains unavailable on this Docker-only host.
- This sprint can improve decision hygiene but cannot prove hardware reality, phone/browser reality, route/elevator delivery, or cloud production readiness.
