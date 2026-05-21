# Cloud Cancel Pending Command Safety Guard PRD

Run time: 2026-05-21 20:05 CST

## User Value

When a phone or cloud operator taps cancel while a collect command is still being accepted by ROS2, the UI must explain that cancel is pending until the goal is accepted. It must not look like a successful cancel, successful delivery, or a retryable generic cloud failure.

## Problem

The cloud command chain already has many fail-closed degraded states, but cancel during `collect_pending` is still a generic `busy`/failed path. That leaves users and support without a named command-safety state, and it weakens the phone-first contract for one of the three primary commands.

## OKR Mapping

- Primary: Objective 5 KR1 / KR6, cloud command/status/ACK semantics and graceful degradation.
- Supporting: Objective 4 KR1 / KR5 / KR7, phone-visible control safety and user-readable failure explanation.
- Non-goal: Objective 1 hardware proof, real O5 external proof, true phone/browser proof, route/elevator field pass, dropoff/cancel completion, delivery result, or delivery success.

## Required Behavior

Robot/API must surface a canonical degraded state when a cloud `cancel` command is received while collect goal acceptance is still pending:

- `capability=cloud_cancel_pending_command_safety_guard`
- `degradation_state=cancel_pending_goal_acceptance`
- `remote_ready=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `retry_hint=wait_for_goal_acceptance`
- `ack_semantics=cancel_pending_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_cancel_pending_command_safety_guard`
- safe Chinese phone copy explaining that cancel should be retried after goal acceptance or handled via support if it remains blocked.

Mobile/web must render this state from safe Robot/API fields and keep Start Delivery, Confirm Dropoff, and Cancel disabled while Diagnostics/Support Handoff remain available.

## Acceptance

The sprint is accepted only if Robot and Full-Stack workers run focused fences and Product closeout records the boundary. No broad regression sweep is required.

## Risks

This remains Docker/local software proof. The local state proves a command-safety branch, not a real cancel completion, real phone/browser result, production cloud behavior, route/elevator field pass, HIL, or delivery success.
