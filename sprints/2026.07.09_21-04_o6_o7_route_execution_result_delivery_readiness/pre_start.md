# O6/O7 Route Execution Result Delivery Readiness Pre Start

## sprint_type: epic

启动时间：2026-07-09 21:04 CST。

## 用户价值和产品北极星

普通手机用户和运营人员最终关心的不是又多了一层只读摘要，而是“同一 `task_id` 的路线执行结果、投递结果和操作员确认，是否已经形成可复盘、可读回、可展示的同一条证据链”。上一轮已经把准现场 DB3 `route_bag_pose_progress_replay` 接到 O6/O7，本轮继续沿着 CEO 指定方向，把下一步优先级切到 `route_execution_result_delivery_readiness`：让离线/fixture/mock 的 route execution result 与 delivery/operator confirmation readiness 从 Algorithm manifest 进入 O6 archive/readback，再进入 O7 consumer/UI。

产品北极星不变：普通用户把垃圾交给机器人后，机器人要可验证地完成垃圾投递。本轮只做 software proof 的结果链路接线，不证明真实 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。

## OKR 映射和方向判断

- 当前最低 active Objective：O6、O7，在 `OKR.md` 4.1 中并列约 68%。
- 方向判断：继续推进 O6/O7，并从 `route_bag_pose_progress_replay` 切到 `route_execution_result + delivery/operator confirmation readiness`。
- O6 对齐：围绕同一 `task_id` 增强 archive/readback 的任务结果与投递确认证据读取能力，让 archive detail、field evidence、artifact bundle 和 `include=` 可以读到统一摘要。
- O7 对齐：让 PC consumer detail / UI 能看到路线执行结果、投递 readiness、operator confirmation readiness、blocked reasons 和 next evidence，而不是继续只堆新的 wrapper。
- KR 历史归档判断：本轮计划阶段不归档任何 KR；即使工程完成，也只能作为 software proof 提升，不足以把 O6/O7 KR 标为完成。

## 上轮完成项和承接点

- `sprints/2026.07.09_20-03_o6_o7_route_bag_pose_progress_replay/final.md` 已完成 `route_bag_pose_progress_replay` 链路，明确下一步优先是：
  1. live Nav2 route execution result；
  2. 真实/离线 delivery record 与 operator confirmation；
  3. production cloud。
- 本轮承接点：不再新增纯回放 wrapper，而是让同一 `task_id` 的 route execution result 与 delivery/operator confirmation readiness 成为 O6/O7 可读回的统一结果面。

## 本轮核心抓手

本轮选择 `route_execution_result_delivery_readiness` 作为 O6/O7 的共用抓手：

- Algorithm 负责把 route execution result、delivery result readiness、operator confirmation readiness 汇总到同一 manifest / packet；
- O6 负责 archive ingest、detail readback、consumer include；
- O7 负责 consumer detail 和只读 UI 展示。

所有输出都必须保持 fail-closed 和 summary-only：只允许状态、计数、短标签、blocked reasons、next evidence、sha256 prefix、false safety fields；不得输出绝对路径、token、完整 payload、控制成功暗示或任何会被误读为真实送达完成的字段。

## 最近两轮 blocker 扫描

- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/final.md`：完成态，不是 blocker 收口。主要剩余缺口是 live Nav2 route execution、delivery/operator confirmation 和 production cloud。
- `sprints/2026.07.09_20-03_o6_o7_route_bag_pose_progress_replay/final.md`：完成态，不是 blocker 收口。明确要求下一步消费 route execution / delivery result，而不是继续叠加只读 wrapper。
- 结论：最近两轮不存在同一 blocker 的重复消费。本轮直接消费结果链路缺口，符合“不要连续消费同一 blocker”的要求。

## Owner 和协同

- `robot-algorithm-engineer`：生成 route execution result + delivery/operator confirmation readiness 的安全摘要，并写入 manifest / field packet。
- `robot-software-engineer`：把上述摘要接入 O6 archive/readback/include，保持 additive 和 fail-closed。
- `full-stack-software-engineer`：在 O7 consumer detail / UI 展示统一结果链，只读呈现 readiness、blocked reasons、next evidence 和 false safety fields。
- `product-okr-owner`：工程 owner 返回后统一验收并补 `tech-done.md`、`side2side_check.md`、`final.md`；当前只创建本轮前三份 epic 文档。

## 验收边界

- 必须围绕同一 `task_id` 形成 Algorithm -> O6 -> O7 的 `route_execution_result_delivery_readiness` 证据链。
- 必须显式保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 必须明确这是 local/fixture/mock software proof，不连接 production cloud，不发布 `/cmd_vel`，不下发 live Nav2 goal，不声称真实 robot motion 或真实投递完成。
- 不把 readiness、archive readback、consumer display 写成真实 delivery record、真实 operator confirmation 或真实 delivery success。
