# Pre Start - O6/O7 Label Query Filters

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_11-13_o6_o7_label_query_filters/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `full-stack-software-engineer`
- Supporting owner: `full-stack-software-engineer` for O7 adapter/tests only if the consumer path needs query semantics exposed
- Plan status: planning_only
- Start time: 2026-07-13 11:13 CST
- Proof boundary: `software_proof_o6_o7_label_query_filters_only`

## User Value and Product North Star

North star stays unchanged: a normal phone user can hand trash to the robot, the robot can follow a fixed route, and the resulting task evidence can be reviewed and improved without requiring ROS2 or shell knowledge.

This sprint does not move the robot. Its value is narrower: O6/O7 labeling needs a reliable local/mock query contract so operators can find label records by `robot_id`, `task_id`, and `date` instead of scanning a broad list. This supports O6 KR2 and O7 labeling review workflows, but it remains software-proof archive hardening.

## Background and Blocker Scan

Current OKR lowest active item is O5 at about `85%`, but O5 is still blocked on external production evidence:

- real public HTTPS/TLS ingress
- real 4G/SIM path
- production DB/queue
- production worker cutover
- OSS/CDN live traffic
- real phone/browser evidence

Recent O1/O3 runs already consumed the current stop path readiness and mock-only stop HIL capture gate:

- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/`
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/`

Those runs ended with the next step requiring explicit operator approval, current live `/api/base/stop`, same-window UART zero-stop frame capture, post-stop `T=1001` L/R zero feedback, and HIL acceptance. The current environment cannot provide that live operator/hardware evidence, so repeating stop-path readiness or mock-only stop HIL capture would violate the repeated blocker rule.

Automation memory also says not to repeat helper/export/readiness/route-intent, packet packaging, bounded-plan packaging, stop-path readiness, mock-only stop HIL capture gate, or O6/O7 readback-only wrapper. The old O6 triage found a concrete unimplemented gap: `GET /api/o6/archive/labels` only handled `status` and `limit`; O6 KR2 needs task record and labeling results queryable by `robot_id`, `task_id`, and `date`.

## OKR Mapping and Direction Judgment

- O5: pause for this run. Direction is blocked, not replaced. No new external production evidence is available.
- O6: continue. This sprint targets O6 KR2 data/query usability for local/mock archive labels.
- O7: continue only as a consumer of the O6 contract if needed. O7 must remain observe-only and fail-closed.
- O1/O3: pause for this run because the next useful step requires explicit operator approval and current live HIL inputs.
- Direction judgment: adjust sprint target from lowest blocked O5 / blocked current live HIL lane to the next movable O6/O7 software gap. Do not change OKR percentages during planning.
- KR archive judgment: no KR can be archived by planning. Later implementation may still be support-only unless it produces stronger evidence than a local/mock query contract.

## KR Breakdown

O6 KR2 gap for this sprint:

1. `GET /api/o6/archive/labels` must support optional `robot_id`.
2. `GET /api/o6/archive/labels` must support optional `task_id`.
3. `GET /api/o6/archive/labels` must support optional `date`.
4. New filters must compose with existing `status` and `limit`.
5. Invalid or unsafe query values must fail closed without leaking raw payloads, tokens, paths, tracebacks, or unrelated labels.

O7 minimal gap:

- If the O7 consumer adapter or tests read label list semantics, add the smallest verification that the O7 path preserves filtered O6 results and does not display labels outside the requested `robot_id`, `task_id`, or `date`.
- No new O7 action, submit, export, send, command, route execution, delivery, or production cloud capability is in scope.

## Core Lever

The core lever is `label query filters`: make O6 local/mock labeling data searchable by identity and date while preserving fail-closed, not-proven, and fixed-false safety fields.

This is not production cloud, not real robot data, not route execution, not delivery, not HIL, and not a route-intent/readback wrapper.

## Scope Boundaries

Allowed in the later implementation sprint:

- O6 label list API query parsing and response contract around `/api/o6/archive/labels`
- O6 relay unit tests and local/mock store tests
- O6 interface documentation
- O7 adapter/tests only if needed to verify filtered label semantics

Out of scope:

- Production DB/queue, public HTTPS/TLS, 4G/SIM, OSS/CDN, worker cutover, real browser/mobile evidence
- Real robot archive data, true cloud annotation API, true dataset export
- Route execution, fixed-route movement, NavigateToPose, controller/BT, `/cmd_vel`, `/api/base/manual`, WAVE ROVER UART
- Delivery success, operator acceptance, HIL, safe-to-control
- Another helper/export/readiness/route-intent, packet packaging, bounded-plan packaging, stop-path readiness, mock-only stop HIL capture gate, or O6/O7 readback-only wrapper

## Responsibility

Primary owner: `full-stack-software-engineer`.

Rationale: the work is concentrated in O6 archive API, local/mock relay tests, docs/interfaces, and optional O7 consumer adapter tests. Hardware, Algorithm, and Robot Software should not be involved unless the implementation unexpectedly touches robot runtime or ROS2 contracts, which it should not.

## Sprint Documents

This planning run creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Later implementation must create or update `tech-done.md` with actual changes and verification. Epic closeout must then update `side2side_check.md` and `final.md` only after implementation evidence exists.
