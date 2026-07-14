# PRD - O3 Fixed Route Intent Replay Material

## Summary

本 sprint 延续 `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/` 的 Product acceptance。上一轮已接受为 O3/O1 strict no-motion same-run planner-only path proof：

- `status=nav2_no_motion_path_generation_runtime_observed`
- `evidence_type=robot_runtime_material`
- `managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start`
- `scan_once_observed=true`
- `map_once_observed=true`
- `amcl_pose_observed=true`
- `initialpose_published=true`
- `map_to_odom=true`
- `path_generation_attempted=true`
- `path_generated=true`
- `path_point_count=21`
- `fallback_used=true`
- `fallback_mode=ros2_cli_action_send_goal`
- `root_causes=[]`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

本轮 PRD 要求 `robot-algorithm-engineer` 把这份 same-run planner-only path proof 转成可验收的 fixed-route replay / route-intent material。材料必须能被后续 route execution、delivery/operator acceptance、O6 archive/readback 或 O7 replay 消费，但本轮本身仍是 strict no-motion，不是 route execution。

## 用户价值和产品北极星

北极星：普通手机用户不懂 ROS2、不看 SSH、不管硬件细节，也能把垃圾交给小车，一键发车后得到可验证的送达或失败结果。

上一轮证明“同一轮可以规划出路径”，但用户价值还没有走到“这条路径可以成为一个固定路线任务”。本轮的产品价值是把 21 点 planner path 变成 route-intent / replay material：后续每个 Engineer 可以围绕同一条 `route_intent_id` 或 `task_id` 继续推进执行、归档、可视化和验收，而不是在不同证据包之间人工对齐。

## Problem

21:57 的成功证据仍停在 planner-only path proof：

1. 它证明 ComputePathToPose 可以在 strict no-motion 条件下生成 21 个 path points。
2. 它没有证明 NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、route execution、delivery、HIL 或 safe-to-control。
3. 它还没有形成固定路线回放、route.csv、replay JSONL、任务意图、next evidence gate 或同一 `task_id` 的材料入口。

Product 的核心需求是：把 path proof 转成下一轮能消费的路线意图材料，同时把不允许声明的范围写死，避免 planner-only proof 被误读成路线执行或送达。

## Scope

In scope for `robot-algorithm-engineer`:

- 读取或消费 21:57 accepted source path proof artifact。
- 生成本轮 artifact，至少包含 JSON summary。
- 生成 replay JSONL 或 `route.csv` 中至少一种可消费路线材料。
- 生成或记录 `route_intent_id` / `task_id`。
- 摘要 planned waypoint / pose / path point count / frame / start source / goal summary。
- 明确 source path proof ref，指向 21:57 artifact 或 sprint evidence。
- 明确 fixed-route / route-intent summary，说明 material 如何被下一轮 route execution 或 replay 消费。
- 明确 `next_evidence_required`：route execution record、delivery/operator acceptance、current live HIL、production readback 等。
- 明确 no-motion false fields：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false` 等。
- 更新 navigation docs 和本 sprint `tech-done.md`。

Out of scope:

- O5 production/cloud support-only、cutover readiness、external probe wrapper。
- Full-stack/O7 独立 UI surface、handoff、status panel 或 checklist。
- WAVE ROVER、ESP32、UART、serial、baudrate、wiring、电压、vendor-backed hardware edits。
- `/cmd_vel`、`/api/base/manual`、NavigateToPose、controller/BT、route execution、delivery command 或 WAVE ROVER UART。
- 宣称 safe-to-control、current live HIL、delivery success、production external evidence。
- 修改 `OKR.md`、`docs/process/okr_progress_log.md` 或历史 sprint。

## OKR Mapping And Direction Judgment

- O5 是当前最低 Objective，约 `85%`；本轮不做 O5，因为缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。继续 support-only 不应计分。
- O3/O1 strict no-motion 是本轮最高可执行抓手，因为上一轮刚拿到 current same-run planner-only path proof，下一步最自然的用户价值台阶是 fixed-route replay / route-intent material。
- 方向判断：继续 O3/O1，暂停 O5 support-only，冻结独立 O6/O7 surface。
- OKR 口径：本轮即使成功产出 route-intent material，也默认只算 supporting evidence，O5/O1/O6/O7 百分比保持 flat；只有后续产生 route execution、delivery/operator acceptance、current live HIL 或 real production external evidence，才进入 Product percentage review。

## Acceptance Criteria

P0 accepted outcome must satisfy all:

- 产出本轮 artifact，建议包含：
  - `route_intent_summary.json`
  - `route_intent_replay.jsonl` 或 `route.csv`
- Artifact 包含 `route_intent_id` 或 `task_id`。
- Artifact 包含 `source_path_proof_ref`，引用 21:57 source proof。
- Artifact 明确 `path_generation_attempted=true`、`path_generated=true`、`path_point_count=21`、`fallback_mode=ros2_cli_action_send_goal` 是 source evidence，而不是本轮 route execution。
- Artifact 包含 planned waypoint/pose summary，至少能让下一轮判断 route 起点、终点、点数、frame 和顺序。
- Artifact 包含 fixed-route / route-intent summary，能被后续 route execution 或 replay 消费。
- Artifact 明确 `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。
- Artifact 明确 `next_evidence_required`，至少包括 route execution record、delivery/operator evidence、current live HIL 或 production readback 中的下一步。
- `tech-done.md` 记录实际改动、验证命令、失败定位和剩余风险。

Accepted blocked outcome:

- 如果无法从 source proof 提取完整 pose/waypoint，Product 只接受更窄 blocker：缺 source artifact、缺 path field、field schema drift、或 route material writer failure，并且必须给出下一条修复命令。

Rejected outcomes:

- 只复述 21:57 final 而没有本轮 route-intent artifact。
- 只生成 checklist、handoff、owner response、readback summary 或状态面板。
- 把 planner-only path proof 说成 route execution、NavigateToPose、controller/BT、delivery、HIL 或 safe-to-control。
- 任何 motion/control action。
- 回到 O5 support-only 或 O6/O7 独立 surface。

## KR 拆解、更新或历史归档

本 planning pass 不归档任何 KR。当前 KR 历史位置保持不变：

- 已完成或归档 Objective/KR 仍在 `OKR.md` 的历史/归档区和 `docs/process/okr_progress_log.md`。
- 21:57 sprint 已接受为 O3/O1 strict no-motion same-run planner-only path proof，但 `不归档` KR。
- 本轮只允许新增 O3/O1 route materialization supporting evidence。
- O5 继续约 `85%`，O1 继续约 `94%`，O6/O7 继续约 `93%`，除非 implementation 意外产生 stronger mission evidence 并经 Product 复核。

## Risks And Evidence Gaps

- Source artifact schema 可能只适合 path proof，不直接适合 route replay。
- 21 个 path points 可能缺少 fixed-route 所需的人类可读 waypoint 名称、路线段语义或 route metadata。
- route-intent material 不等于 Nav2 goal execution，仍不能证明 controller/BT、`/cmd_vel` 或底盘运动。
- 当前没有 route execution record、delivery/operator acceptance、current live HIL、safe-to-control、真实手机/browser action、production cloud 或 external evidence。
- 如果本轮只得到 partial material，必须明确 next evidence required，不能用“材料存在”替代路线执行成功。
