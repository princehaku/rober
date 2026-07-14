# Pre Start - O3 28-Pose Fixed Route Consumer

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Status: planning complete, ready for single-owner Algorithm implementation
- Start time: 2026-07-13 04:02 CST

## 用户价值和产品北极星

产品北极星是让普通手机用户最终可以一键发起固定路线送垃圾任务，并拿到可验证、可复盘的送达或失败结果。本轮不做发车和送达，只把 03:00 fresh same-run `28-pose` structured path material 接到 fixed-route / route-intent consumer，减少对旧 21:57 partial stdout-tail 的依赖。

用户价值是把路线证据链从“planner-only path artifact 已存在”推进到“fixed-route consumer 能消费完整 structured poses 并输出同一任务材料”。这为下一步 route replay 或受控 route execution 准备更可靠的 artifact 输入。

## 上轮事实和未完成项

上一轮 `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/` 已完成 Product acceptance closeout：

- fresh same-run artifact 已使用：`fresh_live_artifact_used=true`
- 旧 21:57 artifact 未作为 live proof 复用：`historic_21_57_artifact_reused_as_live_proof=false`
- planner-only no-motion path 已生成：`path_generated=true`
- path count 为 `28`：`path_point_count=28`、`path_structured_pose_count=28`
- original `21` 点目标未复现，exact blocker 为 `expected_21_structured_pose_count_not_reproduced_current_live_returned_28_after_map_bounds_adaptation`

01:00 `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/` 只能消费旧 route-intent partial material，边界是 `full_structured_path_poses_missing`。因此本轮必须消费 03:00 的 fresh `28-pose` material，而不是继续包装旧 21:57 stdout-tail。

## OKR 映射和方向判断

- Objective 5：当前最低，约 `85%`，但真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser 证据未到位。继续做 readiness/checklist/wrapper 会重复消费 support-only blocker，本轮不推进 O5。
- Objective 1：约 `94%`。本轮可作为 O3/O1 strict no-motion fixed-route consumer material 的相邻链路，但不能证明 current live HIL、safe-to-control、route execution 或 delivery。
- O3 现场验证 lane：临时激活。本轮方向是继续，把 fresh 28-pose structured material 接入 fixed-route / route-intent consumer。
- 方向判断：继续 O3/O1 strict no-motion lane，暂停 O5 support-only wrapper，不归档 KR。

## 本轮核心抓手

核心抓手是让 `robot-algorithm-engineer` 单 owner 闭环：

1. 读取 03:00 summary artifact 的 `path_structured_poses` / `path_structured_pose_count=28`。
2. 生成或更新 fixed-route / route-intent consumer artifact，使 consumer 优先消费 fresh 28-pose structured poses。
3. 输出 `task_id`、`route_intent_id`、route replay JSONL/CSV 或等价 dry-run summary，并明确不依赖旧 21:57 partial stdout-tail。
4. 固定 no-motion safety fields：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。

## 范围边界

允许进入后续实现的范围：

- Algorithm artifact consumer / route-intent material / fixed-route dry-run consumer。
- 与上述 artifact 直接相关的 tests、sprint `tech-done.md` 和必要导航文档同步。

明确禁止：

- 不触发 route execution、NavigateToPose、controller/BT。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不声明 delivery/operator acceptance、HIL、safe-to-control 或 O5 production/external evidence。

## 风险和阻塞

- 28-pose 与原 21-pose expectation 不一致，consumer 必须接受可变 path shape，不能硬编码 21。
- 03:00 material 的 blocker 来自 current live localization/map-bound drift，本轮 consumer 只能消费该 material，不能解决真实定位漂移。
- 本轮仍是 software/artifact consumer，不产生 route runtime log、delivery record、operator acceptance 或 HIL pass。
- O5 仍缺真实 external production evidence，本轮不能提升 O5 或归档 O5 KR。

## 本轮需要创建或更新的 sprint 文档

- `pre_start.md`：本文件，记录目标、owner、边界和 blocker。
- `prd.md`：定义产品需求、验收口径和 KR 判断。
- `tech-plan.md`：给 `robot-algorithm-engineer` 的单 owner 实现计划、文件范围、验收命令和 OKR 最低优先级核对。
