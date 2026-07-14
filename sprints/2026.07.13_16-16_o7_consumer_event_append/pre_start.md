# Pre Start - O7 Consumer Event Append

## Sprint Type

- sprint_type: epic
- Sprint: `sprints/2026.07.13_16-16_o7_consumer_event_append/`
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Planned status: planning only; do not create `tech-done.md`, `side2side_check.md`, or `final.md` in this phase.

## User Value And North Star

The product north star is still a low-cost ROS2 trash delivery robot that a normal phone user can operate, with every mission event observable and replayable. This sprint does not move the robot or prove delivery; it gives the PC/O7 selected-task workflow a safe local/mock action for appending mission events to the O6 archive, so a later operator can attach concrete task evidence instead of only reading summaries.

User value: an operator viewing a selected task can append a bounded mission event with `task_id`, `robot_id`, `event_id`, `event_type`, `evidence_ref` or `evidence_refs`, and `occurred_at_ms`, then receive a receipt that proves the event was accepted into the local/mock O6 archive path.

## Context And Prior Blockers

- Current `OKR.md` 4.1 lowest Objective is O5 at about `85%`.
- The latest O5 sprint `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/` closed on `blocked_http_status_not_success_class`; repeating O5 without success-class public endpoint, production DB/queue, worker cutover, OSS/CDN, 4G/SIM, or real phone/browser evidence would consume the same blocker again.
- O1/O3 route execution and HIL remain blocked on explicit operator approval, current live stop/HIL, same-window LiDAR/localization/TF readiness, and Nav2/controller result. This automation must not trigger hardware or motion.
- Recent completed work must not be repeated: O6/O7 label/task query filters, O7 consumer-read filters, O7 inference request, O5 CDN/TLS 4xx probe, stop-path/mock HIL gate, route packet or bounded-plan packaging/readback.

## Direction Decision

Direction: adjust this hourly run away from O5 and O1/O3, and continue with a distinct O7/O6 action-write software increment.

Reason: the selected task mission-event append path is not another readback/query wrapper. It consumes mission identity fields and writes to the existing O6 `POST /api/o6/archive/events` local/mock archive contract, while preserving all false safety and production fields.

## This Sprint Target

Create an Epic plan for PC/O7 selected-task `mission event append`:

- O7 exposes a selected-task action endpoint for appending one local/mock mission event.
- O7 Node adapter validates local-loopback base URL and fail-closes unsafe body, task mismatch, unsupported event type, unsafe refs, raw payload content, and dangerous true claims.
- O7 forwards only the fixed O6 endpoint `POST /api/o6/archive/events`.
- O7 returns a safe receipt proving local/mock event append or update only.
- The sprint must explicitly preserve `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, and `robot_control_executed=false`.

## Non Goals

- No production cloud, production DB/queue, OSS/CDN, 4G/SIM, or real phone/browser proof.
- No real robot data claim.
- No route execution, delivery success, HIL, safe-to-control, or operator acceptance claim.
- No `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or primary actions.
- No OKR percentage adjustment and no KR archival in the plan phase; expected closeout wording remains `不归档` unless later implementation produces stronger evidence than planned.
