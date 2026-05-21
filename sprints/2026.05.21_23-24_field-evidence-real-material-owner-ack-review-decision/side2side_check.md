# Field Evidence Real Material Owner Ack Review Decision Side2Side Check

## Acceptance Summary

- sprint_type: epic
- capability: `field_evidence_real_material_owner_ack_review_decision`
- evidence_boundary: `software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate`
- decision: accepted as Docker/local software proof only

## User Value Check

The PRD asked for a structured review step after field owner acknowledgement. This sprint satisfies that product need by turning `field_evidence_real_material_owner_ack_intake` into a conservative review decision vocabulary:

- `accepted`
- `needs_more_evidence`
- `rejected`

The user value is clearer handoff for field materials: support and field owners can see whether an acknowledgement is structurally enough for the next review/backfill step, what evidence remains missing, and who owns the next action. The UI and diagnostics do not ask ordinary users to inspect raw JSON, ROS topics, serial details, or hardware internals.

## Product North Star Check

The product north star remains ordinary-phone operation for a low-cost ROS2 trash delivery robot. This sprint supports that north star by making field-material review status visible in PC tools, Robot diagnostics, and mobile/web while keeping primary actions fail-closed.

This does not move the robot, does not validate the route/elevator field run, and does not prove real phone/browser behavior. It only improves the evidence chain that future real field materials must satisfy.

## OKR Mapping Check

| Objective | Check Result |
| --- | --- |
| Objective 1 | No progress increase. Hardware consultation confirms no WAVE ROVER/UART/HIL/2D LiDAR/ToF claim, and PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending. |
| Objective 2 | Product surface improved for field-material review decisions, but no true task record, elevator field pass, dropoff/cancel completion, delivery result, or delivery success was produced. |
| Objective 3 | The review decision can require Nav2/fixed-route logs and route completion signal under the same safe `evidence_ref`, but no real route runtime evidence was produced. |
| Objective 4 | mobile/web now shows a read-only "现场材料 owner ack 复核决策" panel and keeps Start Delivery / Confirm Dropoff / Cancel disabled, but this is not true phone/browser proof. |
| Objective 5 | No progress increase. This sprint is not real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or true phone/browser proof. |

## Acceptance Criteria Check

- The review decision vocabulary is exactly `accepted`, `needs_more_evidence`, and `rejected`: accepted.
- All outputs preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`: accepted.
- Mobile/web Start Delivery, Confirm Dropoff, and Cancel remain disabled: accepted.
- Hardware consultation reads local vendor boundary and makes no hardware-proof claim: accepted.
- Docs under `docs/interfaces/`, `docs/product/`, and PC README were updated by the implementation owners: accepted.
- OKR percentages are unchanged: accepted.

## Proof Boundary

This sprint is `software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate`.

It is not HIL, not WAVE ROVER/UART proof, not true route/elevator field pass, not true phone/browser proof, not O5 external proof, not PR #5 resolved, not delivery result, and not delivery success.

## Side2Side Result

The sprint passes Product side-by-side acceptance for a conservative software-proof review-decision capability. The remaining work is to obtain real materials and rerun the downstream intake/review chain with the same safe `evidence_ref`.
