# Pre Start - O3 Lifecycle-Active Graph Readback Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/`
- Planned start: `2026-07-12 18:56 CST`
- Product owner: `product-okr-owner`
- Implementation owner: `Robot Software`
- Sprint boundary: O3/O1 strict no-motion lifecycle-active graph/readback repair only.
- Single-owner exemption: this sprint is intentionally assigned to one owner because the file scope is concentrated in the no-motion helper, targeted helper tests, navigation docs, and artifact chain. The interface coupling is strong: graph probe timing, lifecycle-active log readback, downstream topic gates, and fail-closed safety fields all live in one helper contract. Robot Software single-line closure is lower risk than splitting the same helper/test/docs surface across multiple agents. This is not fake parallelism; Algorithm waits for graph/topic readback to become clean enough for AMCL/TF/path work, and Hardware waits unless LiDAR serial/runtime/wiring becomes primary with vendor-backed evidence.

## User Value And North Star

The product north star remains a normal phone user handing trash to the robot, starting one fixed-route delivery, and getting a verifiable arrival or failure result without knowing ROS2, SSH, maps, or hardware details.

The current shortest user-value blocker is no longer map-server lifecycle activation. The 17:55 true-board artifact proved `/map_server active=true` and `amcl_active=true`; the next blocker is `managed_runtime_graph_probe_timeout_after_lifecycle_active_log`, which prevents clean `/scan`, `/map`, `/amcl_pose`, `/tf`, planner-only path generation, route execution, delivery/operator acceptance, and current live HIL evidence.

## Evidence Read First

- `AGENTS.md`: requires sprint留档, validation evidence, strict no-motion boundaries, and owner routing.
- `OKR.md`: O5 remains lowest at about `85%`, but support-only packets cannot create OKR credit without real external production evidence.
- `docs/process/iteration_velocity.md`: Epic sprint must include full pre-start, PRD, tech-plan, tech-done, side2side, and final chain; repeated blockers cannot be consumed blindly.
- `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/final.md`: accepted only as O3/O1 strict no-motion blocker narrowing; primary blocker was `map_server_on_configure_return_false_after_valid_map_io_deferred_completion`.
- `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/final.md`: supersedes 16:55 for routing; lifecycle is now active, and the new primary blocker is `managed_runtime_graph_probe_timeout_after_lifecycle_active_log`.

## OKR Mapping And Direction

- O5: direction is paused for this sprint despite being the lowest objective at about `85%`. The available O5 work is still production-readiness/support-only without HTTPS/TLS, public ingress, production DB/queue, worker cutover, OSS/CDN live traffic, real phone/browser, or external production evidence.
- O1/O3: continue the strict no-motion live-board evidence chain. This sprint targets the lifecycle-active graph/readback gate that blocks same-run path generation and route execution evidence.
- O6/O7: remain waiting on stronger live route, delivery/operator, or production readback material; no read-only surface, handoff, or checklist sprint should be counted as progress.
- Direction judgment: continue O3/O1, adjust away from O5 support-only, and do not replace the active blocker with older map-server lifecycle labels.

## Core Handle

Robot Software must fix or decide the lifecycle-active graph/readback timeout:

`managed_runtime_graph_probe_timeout_after_lifecycle_active_log`

Accepted next outcomes:

- Preferred: graph/readback becomes clean enough to prove the next downstream gate.
- Acceptable blocked outcome: root cause is narrowed beyond lifecycle-active graph timeout into a concrete downstream gate such as `/scan_no_publisher`, `/map_once_not_observed`, `/amcl_pose_topic_missing`, `/tf_topic_missing`, or an explicit graph daemon/DDS/readback budget issue.
- Rejected outcome: re-labeling the primary blocker as `map_server_lifecycle_not_active`, `map_server_on_configure_return_false_after_valid_map_io_deferred_completion`, or `map_server_changestate_response_false_before_map_io_completion` without new true-board evidence that overturns 17:55.

## Safety Boundary

This sprint is strict no-motion:

- Do not publish `/cmd_vel`.
- Do not call `/api/base/manual`.
- Do not send NavigateToPose.
- Do not open or use WAVE ROVER UART.
- Keep `safe_to_control=false`, `publishes_cmd_vel=false`, `calls_base_manual=false`, `uses_base_uart=false`, `robot_control_executed=false`, `route_execution_success=false`, `delivery_success=false`, and `hil_pass=false` unless a later explicitly motion-approved sprint changes scope.

## Required Sprint Documents

This planning pass creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Implementation closeout must later create/update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
