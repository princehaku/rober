# Pre Start - O3 Fixed Route Consumer Dry Run

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Sprint goal: consume the 00:00 route-intent packet in a strict no-motion fixed-route consumer dry-run, or produce stronger full structured path material if the consumer is blocked by partial pose materialization.

## User Value And Product North Star

用户价值不是再写一层 route-intent 说明，而是让固定路线材料进入可消费状态：下一轮 Engineer 能围绕同一个 `route_intent_id` / `task_id` 判断路线是否可被 dry-run consumer、O6/O7 archive/readback 或后续 route execution sprint 正确读取。

产品北极星仍是普通手机用户一键发车后，小车能给出可验证的送达或失败结果。本 sprint 处在路线执行前一格：把 planner-only path proof 和 route-intent packet 推进到 consumer dry-run/material validation，仍不能宣称路线执行、送达、HIL 或 safe-to-control。

## Required Reading Completed

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/final.md`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/tech-done.md`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/tech-plan.md`
- `/Users/m1/.codex/automations/rober-okr/memory.md`

## Previous Sprint Facts To Preserve

- Source sprint: `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/`
- Route intent: `route_intent_20260713_0000_from_20260712_2157_path_proof`
- Task: `task_o3_fixed_route_intent_20260713_0000`
- Source path proof fields: `path_generation_attempted=true`, `path_generated=true`, `path_point_count=21`, `fallback_mode=ros2_cli_action_send_goal`
- Accepted artifacts: `route_intent_summary.json`, `route_intent_replay.jsonl`, `route.csv`
- Accepted boundary: `software_proof_o3_o1_strict_no_motion_route_intent_material_only`
- Partial material boundary: `path_pose_materialization_status=partial_stdout_tail_only`, `materialized_stdout_tail_pose_count=14`, `minimum_unmaterialized_path_pose_count=7`

## Direction Judgment

- Continue: O3/O1 strict no-motion mission-material lane.
- Pause: O5 support-only/readiness/checklist/wrapper work, because O5 still lacks real external production evidence and remains `okr_credit_allowed=false` for support-only material.
- Do not start: independent O6/O7 UI, archive surface, handoff, owner response, intake, or checklist work unless it directly consumes this route-intent packet.
- KR decision for planning: no KR is completed or archived by planning docs. History remains in `OKR.md` and `docs/process/okr_progress_log.md`.

## Core Lever

本轮核心抓手是让 `robot-algorithm-engineer` 执行一个 artifact-only or dry-run-only consumer validation:

1. Read the 00:00 route-intent summary, JSONL, and CSV.
2. Validate identity consistency across `route_intent_id`, `task_id`, source proof ref, path count, frame/order, and no-motion false fields.
3. Emit a consumer dry-run summary/JSONL/CSV that proves the packet can be consumed without motion, or emit stronger full structured path poses if partial stdout-tail material blocks dry-run quality.
4. Record exact next evidence needed for later route execution, delivery/operator acceptance, current live HIL, or production readback.

## Strict No-Motion Boundary

This sprint is strict no-motion. Implementation must preserve:

- no `/cmd_vel`
- no `/api/base/manual`
- no NavigateToPose
- no controller/BT execution
- no WAVE ROVER UART
- no hardware config edits
- no route execution claim
- no delivery claim
- no HIL pass claim
- no safe-to-control claim

Required false fields for any artifact or closeout:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Sprint Document Plan

This planning step creates only:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Implementation and closeout should later add `tech-done.md`, `side2side_check.md`, and `final.md` only after `robot-algorithm-engineer` produces and verifies material.
