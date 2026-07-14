# Pre Start - O3 Fixed Route Intent Replay Material

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/`
- Planned start: `2026-07-13 00:00 CST`
- Context note: the triggering automation context still refers to `2026-07-12`, but this sprint is created at the local machine time `2026-07-13 00:00 CST`.
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Sprint boundary: O3/O1 strict no-motion fixed-route / route-intent material only.
- Single-owner plan: `robot-algorithm-engineer` owns this sprint because the accepted input is a Nav2 planner-only path proof and the next product value is route materialization, not platform readback, hardware config, cloud surface, or UI work.

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给小车后，一键发车并得到可验证的送达或失败结果。21:57 sprint 已把真实上位机链路推进到 same-run planner-only path proof；本轮要把那条 21 点路径转成可复核的 fixed-route replay / route-intent material，让下一轮可以围绕同一条 route intent 讨论路线执行、送达、HIL 或生产证据，而不是继续反复解释 path proof 的边界。

本轮不交付真实运动，也不让用户发车。它交付的是从 planner-only path 到路线意图材料的产品证据台阶：至少要有 `route_intent_id` 或 `task_id`、source path proof 引用、waypoint/pose 摘要、route replay/intent summary、no-motion false fields 和 next evidence required。

## Read First Evidence

- `AGENTS.md`: 每轮必须归入 sprint，Epic 需要完整计划链路；实现、测试、修复由一线 Engineer 执行；strict no-motion lane 不得发 `/cmd_vel`、不得调用 `/api/base/manual`、不得触碰 WAVE ROVER UART。
- `OKR.md`: 4.1 当前最低 Objective 是 O5 约 `85%`，但缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence；继续 O5 support-only 不应计分。
- `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/tech-done.md`: final artifact `live_o10_reuse_existing_lidar_lifecycle_path_proof_after_fallback.raw.json` 已证明 `path_generation_attempted=true`、`path_generated=true`、`path_point_count=21`、`fallback_mode=ros2_cli_action_send_goal`，并继续固定 no-motion 安全字段 false。
- `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/final.md`: Product 接受为 O3/O1 strict no-motion same-run planner-only path proof；拒绝为 route execution、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence；KR `不归档`。
- Automation memory: 下一步应把 same-run planner-only path proof 转成 fixed-route replay 或 route-intent material，优先产出 `route.csv` 或 replay JSONL，并保持 strict no-motion。

## OKR Mapping And Direction

- O5: 继续约 `85%`，本轮不做。原因是 O5 只缺真实 external production evidence；继续 production readiness packet、support-only wrapper、状态面板或 handoff 不产生 `external_artifact_delta`。
- O1/O3: 继续 strict no-motion lane。21:57 已证明 same-run planner-only path generation，本轮把 path proof 转成 route-intent / fixed-route replay material，为 route execution 与 delivery evidence 铺路。
- O6/O7: 暂不安排独立 surface/checklist/handoff。只有当本轮 material 后续被同一 `task_id` 消费到 archive/readback 或 PC replay 时，才进入 O6/O7。
- Direction judgment: 调整执行方向到 O3/O1 route materialization；暂停 O5 support-only；不调整 OKR 百分比；`不归档` KR。

## 本轮核心抓手

`robot-algorithm-engineer` 需要把上一轮 21 个 path points 固化成一个可验收的 no-motion route material packet。推荐产物形态：

- 一个 JSON summary，例如 `route_intent_summary.json`。
- 一个 replay JSONL 或 `route.csv`，至少能表达 planned waypoints / poses / order / source proof。
- Artifact 必须包含 `route_intent_id` 或 `task_id`、source path proof ref、planned waypoint/pose summary、route replay/intent summary、strict no-motion safety fields、next evidence required。

本轮不接受只写说明文、只复述 21:57 final、只包装旧 blocker 或只生成无法被下一轮消费的 checklist。

## Strict No-Motion Safety Boundary

本 sprint 是 strict no-motion material:

- no /cmd_vel。
- no `/api/base/manual`。
- no NavigateToPose。
- no controller/BT route execution。
- no WAVE ROVER UART。
- no route execution claim。
- no delivery claim。
- no HIL pass claim。
- no safe-to-control claim。

Artifact 必须显式保留或派生以下 false 字段：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Required Sprint Documents

本 planning pass 创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 `robot-algorithm-engineer` implementation 需要补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
