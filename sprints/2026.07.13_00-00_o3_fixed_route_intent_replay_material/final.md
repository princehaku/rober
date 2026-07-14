# Final - O3 Fixed Route Intent Replay Material

## Acceptance Result

Product accepts this sprint as O3/O1 strict no-motion route-intent material only.

- Sprint: `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_route_intent_material_only`
- Route intent: `route_intent_20260713_0000_from_20260712_2157_path_proof`
- Task: `task_o3_fixed_route_intent_20260713_0000`
- Direction judgment: continue O3/O1 strict no-motion; pause O5 support-only; do not create O6/O7 surface work until this material is consumed.
- OKR decision: O5 约 `85%`，O1 约 `94%`，O6 约 `93%`，O7 约 `93%`，KR `不归档`.

## 用户价值和产品北极星

用户价值不是“又多一份说明”，而是把上一轮 21 点 planner-only path proof 固化成后续可消费的固定路线意图材料。北极星仍是普通用户一键发车后能得到可验证的送达或失败结果；本轮把路线执行前的材料入口统一到一个 `route_intent_id` / `task_id`，为后续 route execution、delivery/operator acceptance、HIL 和 production readback 建立可复核的同源证据链。

## Evidence Accepted

- Summary schema: `trashbot.route_intent_material.v1`.
- Source evidence: `path_generation_attempted=true`、`path_generated=true`、`path_point_count=21`、`fallback_mode=ros2_cli_action_send_goal`.
- Route material refs: `artifacts/algorithm/route_intent_replay.jsonl` and `artifacts/algorithm/route.csv`.
- JSONL shape: 17 lines, including metadata, request start anchor, 14 materialized stdout-tail poses, and request goal anchor.
- CSV shape: 17 lines including header, 16 route material rows.
- Partial materialization boundary: `partial_stdout_tail_only`; `materialized_stdout_tail_pose_count=14`; `minimum_unmaterialized_path_pose_count=7`.

## Rejected Claims And Safety Boundary

This sprint is not route execution, NavigateToPose, controller/BT execution, `/cmd_vel`, `/api/base/manual`, WAVE ROVER UART, delivery/operator acceptance, current live HIL, safe-to-control, production external evidence, or full 21-point replay.

Safety fields remain fixed:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## KR And History Decision

No KR is completed or archived. Historical KR records remain in `OKR.md` and `docs/process/okr_progress_log.md`; this sprint adds a current progress note only. The evidence is useful because it creates a reusable route-intent packet, but it is still `software_proof_o3_o1_strict_no_motion_route_intent_material_only`, so it does not prove mission execution.

## Core Lever And Next Work

本轮核心抓手是 `robot-algorithm-engineer` 产出的 artifact-only route material packet。下一步优先级：

1. `robot-algorithm-engineer` 输出 full structured path poses，或基于当前 `route_intent_id` 做 strict no-motion fixed-route consumer dry-run。
2. 之后再进入显式 route execution record；只有 route execution record 才能改变 `route_execution_success=false`。
3. delivery/operator acceptance、current live HIL、safe-to-control 和 production credit 必须分别等待对应 live evidence。

## Remaining Risks

- 只能从 `stdout_tail` materialize 14 个完整 pose blocks，不能声明完整 21 点 replay。
- `route.csv` 和 JSONL 是 no-motion route intent material，不是 Nav2 route execution result。
- O5 仍缺真实 external production evidence；O6/O7 若不消费本轮或更强 live material，只能做回归守护，不应提升进度。

## Sprint Documents Updated

- Created `side2side_check.md`.
- Created `final.md`.
- Updated `OKR.md`.
- Updated `docs/process/okr_progress_log.md`.
