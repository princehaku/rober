# Side2Side Check - O3 Fixed Route Consumer Dry Run

## Acceptance Summary

- Sprint: `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/`
- Product status: accepted as O3/O1 strict no-motion fixed-route consumer dry-run material validation only.
- Proof boundary: `software_proof_o3_o1_strict_no_motion_fixed_route_consumer_dry_run_only`
- Direction judgment: continue O3/O1 strict no-motion; keep O5 support-only paused until real external production evidence exists; do not open O6/O7 surface work unless it consumes this material.
- OKR decision: O5 约 `85%`，O1 约 `94%`，O6 约 `93%`，O7 约 `93%`，KR `不归档`.

## User Value And North Star

用户价值是让 00:00 的 route-intent packet 进入可消费状态，而不是再包装一层说明。普通手机用户的北极星仍是“一键发车后得到可信送达或失败结果”；本轮只完成该证据链里的 consumer dry-run/material validation，距离 route execution、delivery、HIL 和 production acceptance 仍差明确证据。

## Evidence Compared

| Check | Expected | Observed | Product Result |
| --- | --- | --- | --- |
| Source identity | Same `route_intent_id` and `task_id` as 00:00 route-intent sprint | `route_intent_20260713_0000_from_20260712_2157_path_proof` and `task_o3_fixed_route_intent_20260713_0000` preserved | Pass |
| Summary schema | Fixed-route consumer dry-run schema | `trashbot.fixed_route_consumer_dry_run.v1` | Pass |
| Validation status | Consumer validation must pass or fail closed with exact blocker | `validation_status=pass_with_material_boundary` | Pass with boundary |
| Dry-run status | Consumer may accept partial material only if boundary is explicit | `dry_run_status=accepted_partial_material_dry_run` | Accepted partial material |
| Event material | Structured event stream exists | `fixed_route_consumer_dry_run_events.jsonl` has 29 events | Pass |
| Route check material | Structured route row check exists | `fixed_route_consumer_dry_run_route_check.csv` has 16 material rows | Pass |
| Source path material | Preserve 21-point source proof while exposing partial materialization | `authoritative_path_point_count=21`, `materialized_stdout_tail_pose_count=14`, `minimum_unmaterialized_path_pose_count=7` | Pass with boundary |
| Full replay claim | Must not claim full 21-point replay without full structured poses | `full_structured_path_poses_missing` | Correctly blocked |

## Rejected Claims

This sprint is not accepted as full 21-point replay, route execution, NavigateToPose, controller/BT execution, `/cmd_vel`, `/api/base/manual`, WAVE ROVER UART, delivery/operator acceptance, HIL, safe-to-control, or production external evidence.

Safety and mission fields remain fixed:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## OKR Mapping And KR Decision

- O5 remains about `85%`: no real HTTPS/TLS, 4G/SIM, production DB/queue, worker cutover, OSS/CDN live traffic, real phone/browser, or external production evidence was consumed.
- O1 remains about `94%`: this consumes the 21:57 planner-only path proof through a fixed-route material consumer, but does not add route execution, HIL, delivery, or safe-to-control evidence.
- O6/O7 remain about `93%`: no backend archive/readback or PC consumer sprint consumed this new material yet.
- KR history stays in `OKR.md` and `docs/process/okr_progress_log.md`; no KR is completed or archived by this sprint.

## Next Evidence Required

1. Full structured path poses export or new route capture if exact 21-point replay is required.
2. Explicit Nav2/fixed-route route execution record before `route_execution_success` can change.
3. Delivery/operator acceptance evidence before `delivery_success` can change.
4. Current live HIL evidence before `hil_pass` or `safe_to_control` can change.
5. Production cloud/readback evidence before O5/O6/O7 production credit can change.

## Responsible Engineer

- Next primary owner: `robot-algorithm-engineer`
- Product acceptance owner: `product-okr-owner`
- Robot Software support only if helper export is required for full structured path poses.
- Hardware, Full-stack, O6, and O7 remain out of scope unless a future sprint explicitly consumes this material.
