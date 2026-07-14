# Side2Side Check - O3 Fixed Route Intent Replay Material

## Product Acceptance Summary

- Sprint: `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/`
- Product status: accepted as O3/O1 strict no-motion route-intent material only.
- Proof boundary: `software_proof_o3_o1_strict_no_motion_route_intent_material_only`
- Route intent: `route_intent_20260713_0000_from_20260712_2157_path_proof`
- Task: `task_o3_fixed_route_intent_20260713_0000`
- KR decision: `不归档`.

## 用户价值和产品北极星

北极星仍是普通手机用户把垃圾交给小车后，一键发车并得到可验证的送达或失败结果。本轮把 2026-07-12 21:57 的 same-run planner-only path proof 转成同一个 `route_intent_id` / `task_id` 下的 route-intent material，让下一轮可以围绕固定路线意图继续做 no-motion consumer dry-run、route execution record、delivery/operator acceptance、HIL 或 production readback，而不是继续重复解释 path proof 边界。

## Side2Side Acceptance Matrix

| Gate | Expected | Observed | Product decision |
| --- | --- | --- | --- |
| Summary schema | `trashbot.route_intent_material.v1` | `route_intent_summary.json` 使用该 schema | accept |
| Stable identity | `route_intent_id` 和 `task_id` 可复用 | `route_intent_20260713_0000_from_20260712_2157_path_proof` / `task_o3_fixed_route_intent_20260713_0000` | accept |
| Source path proof | 保留 21:57 source evidence | `path_generation_attempted=true`、`path_generated=true`、`path_point_count=21`、`fallback_mode=ros2_cli_action_send_goal` | accept |
| Pose materialization | 不补造缺失 path poses | `partial_stdout_tail_only`，`materialized_stdout_tail_pose_count=14`，`minimum_unmaterialized_path_pose_count=7` | accept with boundary |
| Replay material | JSONL 或 CSV 可被下一轮消费 | `route_intent_replay.jsonl` 17 行；`route.csv` 17 行含 header，16 条 material rows | accept |
| Safety boundary | no-motion false fields 保持 false | `safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`，并固定 no `/cmd_vel` / no `/api/base/manual` / no UART | accept |
| OKR scoring | 支持证据，不涨主分 | O5 约 `85%`、O1 约 `94%`、O6 约 `93%`、O7 约 `93%` | accept, `不归档` |

## Rejected Claims

本轮不接受为 route execution、NavigateToPose、controller/BT execution、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery/operator acceptance、current live HIL、safe-to-control、production external evidence 或完整 21 点 route replay。

关键原因是 source artifact 的 authoritative `path_point_count=21` 成立，但本轮只能从 `stdout_tail` materialize 14 个完整 pose blocks；其余至少 7 个 path poses 未被结构化落盘，不能补造，也不能作为 full 21-point replay 宣称。

## Direction And Owner Check

- OKR direction: 继续 O3/O1 strict no-motion route materialization；暂停 O5 support-only；O6/O7 暂不新增 surface。
- Product judgment: 继续，不调整，不归档。
- Next owner: `robot-algorithm-engineer`.
- Next exact evidence: full structured path pose export 或基于当前 `route_intent_id` 的 strict no-motion fixed-route consumer dry-run；route execution、delivery、HIL、production credit 必须另有 live evidence。
