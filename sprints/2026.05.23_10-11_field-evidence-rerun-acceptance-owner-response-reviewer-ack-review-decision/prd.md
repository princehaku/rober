# Field Evidence Rerun Acceptance Owner Response Reviewer ACK Review Decision PRD

Run time: 2026-05-23 10:11 Asia/Shanghai

## User Value And Product North Star

普通手机用户不应该看到“reviewer ACK 已进入系统”这种内部状态后仍不知道能不能继续操作。产品需要把 reviewer ACK intake 转成明确 review decision：哪些 ACK 可以进入后续复核，哪些需要 reviewer 重分配，哪些需要 field owner 补材料，哪些因为 unsafe claim 必须拒绝，哪些因为 intake 缺失必须阻塞。

North star remains: 手机用户能安全地完成送垃圾任务，并在证据不足时得到清晰、保守、可支持的解释。本 PRD 只推进 evidence-governance software proof，不推进真实送达。

## Problem

Recent evidence shows the system has reviewer ACK intake, but not the review-decision rung after it. Without a decision contract:

- PC/support cannot distinguish accepted ACK review readiness from reassignment or missing-material states.
- Robot diagnostics cannot expose a stable safe alias for the current reviewer ACK decision.
- `mobile/web` cannot show the next read-only panel without risking raw diagnostics or success phrasing.
- Product closeout cannot cleanly state why the branch advanced while still preserving `not_proven` and no OKR percentage lift.

## Evidence-Based Recommendation

Next sprint should deepen the field-evidence rerun acceptance branch into:

`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision`

Evidence:

- `OKR.md` 4.1 shows Objective 5 is lowest at about 68%, but all remaining O5 movement depends on real external proof: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, or verified terminal result.
- Objective 1 is about 81%, but PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this Docker-only host lacks the real 2D LiDAR / ToF and HIL-entry materials that thread requires.
- The latest sprint only refreshed local browser current-panel proof and explicitly produced no OKR percentage lift.
- The previous functional chain already landed reviewer ACK intake, so review decision is the next narrow, actionable software-proof rung.

## OKR Mapping

- Objective 5: not targeted for percentage lift. This sprint is not O5 external proof.
- Objective 1: not targeted for percentage lift. This sprint is not O1 HIL, WAVE ROVER/UART proof, LiDAR/ToF installed proof, or PR #5 resolution.
- Objective 2/3/4: targeted only as software-proof evidence governance for route/elevator field-evidence acceptance. It is not true route/elevator field pass, Nav2/fixed-route runtime pass, true phone/browser proof, dropoff/cancel completion, delivery result, or delivery success.

Expected closeout wording: no OKR percentage lift.

## KR Breakdown

Bounded artifact KR:

- PC gate produces a sanitized reviewer ACK review-decision artifact and summary.
- Robot diagnostics exposes a phone-safe safe alias for the same decision state.
- `mobile/web` shows a read-only panel for the decision and keeps primary controls disabled.
- Docs explain the evidence boundary and runtime contract.
- Closeout records no OKR percentage lift and preserves the unresolved PR #5 boundary.

## Scope

In scope:

- Review-decision states:
  - `accepted_for_reviewer_ack_review_not_proven`
  - `needs_reviewer_reassignment_not_proven`
  - `needs_field_owner_supplement_not_proven`
  - `rejected_unsafe_reviewer_ack_not_proven`
  - `blocked_missing_reviewer_ack_intake_not_proven`
- Fixed boundary and flags:
  - `source=software_proof`
  - `software_proof`
  - `not_proven`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `safe_to_control=false`
  - no OKR percentage lift
- Read-only PC, Robot diagnostics, and mobile consumption.
- Fenced validation only.

Out of scope:

- Real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover.
- Real iPhone/Android or true phone/browser proof.
- Real route/elevator field pass, Nav2/fixed-route runtime pass, verified terminal result, dropoff/cancel completion, delivery result, or delivery success.
- O1 HIL, WAVE ROVER/UART proof, LiDAR/ToF installed proof, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.
- Product code implementation during this planning task.

## Acceptance Criteria

- PC CLI accepts valid reviewer ACK intake summary and emits one of the required review-decision states.
- Unsafe claims, missing intake, evidence-ref mismatch, raw paths, credentials, ROS/control details, or success phrasing fail closed.
- Robot diagnostics exposes only sanitized fields and preserves `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- `mobile/web` displays the decision as read-only support metadata and does not enable Start Delivery, Confirm Dropoff, or Cancel.
- Docs under `docs/interfaces/` and `docs/product/` are updated by the implementation workers.
- `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` in closeout unless live evidence changes.
- Closeout states no OKR percentage lift.

## Priority

P0: Autonomy PC evidence gate and test, because it defines the artifact contract.

P0: Robot diagnostics safe alias and test, because it controls what mobile and support surfaces may consume.

P1: Full-Stack read-only panel and fixture, because it gives phone-safe visibility without changing controls.

P1: Product closeout and OKR/progress log after worker validation, because no percentage lift can be claimed without real materials.

## Responsible Engineers

- Task A: Autonomy Algorithm Engineer
- Task B: Robot Platform Engineer
- Task C: User Touchpoint Full-Stack Engineer
- Task D: Product Manager / OKR Owner closeout later

## Evidence Chain To Complete

- PC artifact and summary prove software review-decision classification only.
- Robot diagnostics proves safe alias exposure only.
- Mobile panel proves read-only consumption only.
- Product closeout proves sprint traceability and no OKR percentage lift.
- Real O5, O1, route/elevator, phone/browser, and delivery proofs remain future external evidence.
