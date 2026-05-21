# Field Evidence Real Material Response Review Decision PRD

Run time: 2026-05-21 16:03 CST

## User Value And North Star

The user value is deciding what a field-owner response means next. After response intake classifies materials, the product still needs a clear review decision: ready for later review, needs more material, rejected for unsafe/mixed evidence, or blocked by unavailable real environment.

The north star remains verified autonomous trash delivery. This sprint does not make the robot deliver trash; it makes the evidence workflow less ambiguous so future real route/elevator, phone, and hardware materials can be reviewed without weakening safety boundaries.

## Product Requirement

Create `field_evidence_real_material_response_review_decision` as a software-proof review-decision layer over `field_evidence_real_material_response_intake`.

It must:

1. Consume only a sanitized response-intake artifact, summary, or Robot diagnostics safe alias.
2. Preserve `source=software_proof`, `status=not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
3. Preserve one same safe `evidence_ref`.
4. Convert intake states into a review decision:
   - `accepted_for_later_review_not_proven` when required materials are accepted, safe, and same-evidence-ref, while still not proving a field pass.
   - `needs_material_backfill_not_proven` when any required material is missing.
   - `rejected_unsafe_or_mixed_response_not_proven` when unsafe text, mixed evidence refs, raw material, success claims, credentials, local paths, serial/UART/WAVE ROVER details, or unsupported schema appear.
   - `blocked_real_environment_unavailable_not_proven` when real field route/elevator/phone/cloud/hardware dependencies are unavailable.
5. Produce owner handoff, next required evidence, decision reasons, blocked claims, and phone-safe copy.
6. Fail closed if no valid prior response-intake source exists.

## OKR Mapping

- Objective 5 remains about 68%. This sprint does not target O5 percentage movement because no real external cloud / 4G / OSS/CDN / production DB/queue / worker / production phone/browser evidence exists.
- Objective 1 remains about 81%. This sprint does not target O1 percentage movement because PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved and real hardware materials are still missing.
- Objective 2/3/4 remain about 99%. This sprint improves the field-evidence workflow for future O2/O3/O4 real-material review, but it is not a real route/elevator field pass, true phone/browser proof, dropoff/cancel completion, delivery result, or delivery success.

## Acceptance

- PC gate emits schema `trashbot.field_evidence_real_material_response_review_decision.v1` and summary schema `trashbot.field_evidence_real_material_response_review_decision_summary.v1`.
- Robot diagnostics exposes only `robot_diagnostics_field_evidence_real_material_response_review_decision_summary` with sanitized fields.
- mobile/web shows a read-only review-decision panel and keeps Start Delivery / Confirm Dropoff / Cancel disabled.
- Docs update the evidence contract, Robot runtime contract, and mobile user flow.
- Sprint closeout records validation and keeps all evidence boundaries conservative.

## Owner Split

- Autonomy owns the PC gate, focused tests, and `docs/interfaces/evidence_contracts.md`.
- Robot owns diagnostics alias/tests and `docs/interfaces/ros_runtime_contracts.md`.
- Full-Stack owns `mobile/web` panel/fixture/tests and `docs/product/mobile_user_flow.md`.
- Hardware owns read-only consultation against `docs/vendor/VENDOR_INDEX.md` and PR #5 hardware-boundary language.
- Product owns closeout docs, `OKR.md`, and `docs/process/okr_progress_log.md` if validation supports conservative closeout.

## Risks

- Review decision wording can accidentally sound like real acceptance. The required wording must keep `not_proven` and say accepted only means later review.
- Hardware-sensitive wording must not cite unsupported sensor, UART, pin, voltage, baudrate, firmware, or mechanical facts.
- This sprint must not become another O5 local wrapper; its scope is field-material response review decision.
