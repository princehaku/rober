# PRD - O3 Lifecycle-Active Graph Readback Repair

## Summary

This sprint continues the O3/O1 strict no-motion true-board chain from the 17:55 closeout. The user value is not a new UI or support packet; it is removing the next technical gate between lifecycle-active Nav2 runtime and same-run fixed-route proof.

Latest accepted fact:

- `/map_server active=true`
- `amcl_active=true`
- `managed_runtime_log_lifecycle_readback.clean=true`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_lifecycle_active`
- Primary blocker: `managed_runtime_graph_probe_timeout_after_lifecycle_active_log`

## Problem

The 17:55 artifact moved beyond the previous map-server on-configure blocker, but ROS graph/downstream readback still cannot cleanly prove `/scan`, `/map`, `/amcl_pose`, `/tf`, AMCL pose, dynamic `map->odom`, or planner-only path generation. As long as graph/readback remains ambiguous after lifecycle-active logs, Product cannot route the next work to Algorithm or claim route/delivery progress.

## User Value And Product North Star

North star: a normal phone user can start a fixed-route trash delivery and get a verifiable result.

This sprint contributes by turning lifecycle-active runtime into a reliable readback surface. It does not deliver user-visible motion. It reduces the uncertainty blocking path generation, route execution, and delivery evidence.

## Scope

In scope for Robot Software:

- Inspect and repair `managed_runtime_graph_probe_timeout_after_lifecycle_active_log`.
- Decide whether timeout is a helper/readback budget issue, ROS daemon/DDS issue, graph probe issue, or downstream topic gate.
- Preserve 17:55 lifecycle-active facts unless new true-board evidence disproves them.
- Keep strict no-motion artifact fields fail-closed.
- Update helper tests and navigation documentation for any new graph/readback contract.
- Produce local and, if reachable, true-board artifacts under this sprint.

Out of scope:

- O5 production readiness/support packet work.
- Product code, UI/API, cloud, O6/O7 surface/checklist work.
- Hardware config, launch parameter changes outside the approved Robot Software scope, WAVE ROVER, ESP32, UART, serial settings, baud rate, or vendor facts.
- Route execution, NavigateToPose, `/cmd_vel`, `/api/base/manual`, or WAVE ROVER UART.

## OKR Mapping And Direction Judgment

- O5 remains the lowest current Objective at about `85%`, but this sprint does not target O5 because the next O5 increment requires real external production evidence. More readiness/support material would stay `okr_credit_allowed=false`.
- O3/O1 strict no-motion is temporarily activated because it can produce stronger same-run evidence toward path generation and route execution without requiring unsafe motion.
- Direction judgment: continue O3/O1. Do not return to O5 support-only. Do not return to `map_server_lifecycle_not_active`, `map_server_on_configure_return_false_after_valid_map_io_deferred_completion`, or `map_server_changestate_response_false_before_map_io_completion` unless a new true-board artifact overturns 17:55.

## Acceptance Criteria

P0 acceptance requires one of these:

- Preferred: true-board strict no-motion artifact proves graph/readback clean enough to proceed to downstream AMCL/TF/path work.
- Acceptable: true-board artifact remains fail-closed but narrows beyond `managed_runtime_graph_probe_timeout_after_lifecycle_active_log` into a concrete, actionable downstream gate.

All accepted outcomes must show:

- strict no-motion safety fields remain false.
- No `/cmd_vel`, `/api/base/manual`, NavigateToPose, or WAVE ROVER UART use.
- Artifact and docs clearly distinguish lifecycle-active evidence from path generation, route execution, HIL, delivery, or production evidence.

Rejected outcomes:

- Repeating old lifecycle blockers without new evidence.
- Claiming mission progress from helper/readback work.
- Handing off to Algorithm before graph/topic readback is clean enough.
- Handing off to Hardware before LiDAR serial/runtime/wiring becomes the primary blocker and vendor docs are read.

## KR And History Handling

No KR should be archived in this planning pass. The completed/historical KR location remains `OKR.md` archived Objective section plus `docs/process/okr_progress_log.md`; this sprint should only add supporting O3/O1 evidence after implementation.

If implementation only improves graph/readback classification, OKR percentages should remain flat. Any future OKR movement requires same-run path generation, route execution, delivery/operator acceptance, current live HIL, or real external production evidence.

## Risks And Evidence Gaps

- Graph readback may still time out after lifecycle-active logs.
- `/scan`, `/map`, `/amcl_pose`, and `/tf` may remain blocked.
- LiDAR serial log noise may become relevant later, but it is not the Product-selected primary blocker now.
- There is still no `route.csv`, keyframe, rosbag, replay JSONL, route execution result, delivery/operator acceptance, current live HIL, safe-to-control proof, or production external evidence.
