# PRD - O3 28-Pose Fixed Route Consumer

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Product status: requirements defined, ready for implementation

## 用户价值和产品北极星

普通手机用户最终需要的是“放垃圾、发车、送达或失败可复盘”。当前还没到发车阶段，本 PRD 的价值是把 fresh same-run planner path 从孤立 artifact 变成 fixed-route consumer 可读的路线材料，降低后续路线回放、受控 route execution 和任务闭环的证据断点。

本轮的北极星指标不是送达成功率，而是路线证据链完整性：consumer 应优先消费 03:00 fresh `28-pose` structured material，并把 no-motion 边界、task identity 和下一步证据缺口写成机器可读结果。

## 背景和问题

01:00 的 fixed-route consumer dry-run 已证明 consumer 可读取 route-intent packet，但输入只有旧 21:57 partial stdout-tail，存在 `full_structured_path_poses_missing`。02:00 已补齐 helper export contract，03:00 则产出 fresh same-run full structured material：

- `path_generated=true`
- `path_point_count=28`
- `path_structured_pose_count=28`
- `historic_21_57_artifact_reused_as_live_proof=false`
- `blocked_reason=expected_21_structured_pose_count_not_reproduced_current_live_returned_28_after_map_bounds_adaptation`

因此下一步不应继续重复旧 21:57 partial material 包装，而应把 28-pose material 接进 fixed-route / route-intent consumer。

## 目标

- P0：fixed-route / route-intent consumer 能读取 03:00 fresh 28-pose structured artifact。
- P0：输出新的 same-run consumer summary，明确 `28-pose`、`fixed-route`、`route_intent_id` / `task_id`、source artifact ref 和 validation status。
- P0：证明 consumer 不依赖旧 21:57 partial stdout-tail；如保留历史 ref，只能作为 comparator。
- P0：固定 no-motion safety fields：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。
- P1：生成 route replay JSONL/CSV 或等价检查材料，行数与 28-pose structured input 一致，且 identity/order/frame 字段可复核。

## 非目标

- 不执行 fixed-route movement。
- 不运行 NavigateToPose、controller/BT 或 route execution。
- 不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER UART。
- 不声明 delivery/operator acceptance、current live HIL、safe-to-control 或 O5 production/external evidence。
- 不把 28-pose material 改写成 21-pose，也不补造缺失的历史 stdout-tail path points。

## OKR 映射和方向判断

- O5 当前最低约 `85%`，但被真实 external production evidence 锁住；本轮方向不选择 O5，避免重复 support-only blocker。
- O1 当前约 `94%`，本轮可增强 strict no-motion route material chain，但不足以提升 HIL、route execution、delivery 或 safe-to-control。
- O3 现场验证 lane 继续作为相邻推进链路。本轮从 path export 转向 fixed-route consumer ingestion。
- 方向判断：继续 O3/O1 no-motion artifact consumer；O5 暂停；KR 不归档。

## KR 拆解、更新和历史归档

当前 KR 不归档。本轮只允许作为 O3/O1 supporting material 记录：

- KR 输入：03:00 fresh same-run `28-pose` structured planner material。
- KR 输出：fixed-route / route-intent consumer 可读的 no-motion material。
- KR 不接受：route execution、delivery、HIL、safe-to-control、O5 production/external proof。

已完成 KR 的历史记录仍以 `OKR.md` 的“已归档 Objective”和 `docs/process/okr_progress_log.md` 为准。本轮不会移动历史 KR；实现完成后如果只产出 consumer material，也仍应写 `不归档`，并保留剩余风险。

## 本轮核心抓手

让 `robot-algorithm-engineer` 把 03:00 fresh structured artifact 作为 primary source：

- primary source：`sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_summary.json`
- consumer direction：fixed-route / route-intent consumer
- output type：summary JSON + route replay JSONL/CSV 或同等 dry-run material
- proof boundary：`software_proof_o3_o1_strict_no_motion_28_pose_fixed_route_consumer_only`

## 优先级和验收口径

P0 验收：

- summary 明确 `path_structured_pose_count=28` 或等价字段。
- summary 明确 fresh 03:00 artifact 是 primary source，旧 21:57 partial stdout-tail 未作为 primary live proof。
- consumer validation status 通过，且输出包含 `route_intent_id` / `task_id`。
- safety fields 固定：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。
- artifact 或文档明确禁止 NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual` 和 WAVE ROVER UART。

P1 验收：

- route replay JSONL/CSV 或等价检查材料能展示 28 个 structured poses 的顺序、frame 和 pose 字段。
- 新材料说明下一步需要 route runtime log、route completion signal、delivery/operator acceptance 或 HIL，不能把本轮当成 delivery。

## 对应责任 Engineer

- 主责：`robot-algorithm-engineer`
- 协作：本轮不需要并行 owner。Robot Software、Hardware、Full-stack 只在下一轮需要 ROS route execution、WAVE ROVER/HIL、手机/PC consumer 时介入。

## 风险、阻塞和需要补齐的证据链

- 28-pose count 与历史 21-pose expectation 不一致，后续 route consumer 不能假设固定 21。
- current live localization/map-bound drift 仍存在，本轮不解决定位漂移，只消费已有 material。
- 缺 route runtime log、Nav2 route execution result、task completion record、operator acceptance、delivery result 和 HIL pass。
- 缺 O5 external production evidence：公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser。
