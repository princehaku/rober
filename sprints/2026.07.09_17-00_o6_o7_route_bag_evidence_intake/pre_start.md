# O6/O7 Route Bag Evidence Intake Pre Start

## sprint_type: epic

启动时间：2026-07-09 17:00 CST。

## 用户价值和产品北极星

普通用户最终要看到的是“垃圾投递任务是否有真实路线材料支撑，并且还缺哪些证据才可以相信送达”。当前 O6/O7 已能消费 field motion、Nav2 goal 和 delivery result 的 local/mock evidence，但最近两轮收口都要求下一步优先消费真实或准现场 `route_bag` / live Nav2 pose progress / delivery record，而不是继续堆 local/mock wrapper。

产品北极星不变：普通手机用户把垃圾交给机器人后，机器人要可验证地完成垃圾投递。本轮只做 `route_bag_evidence` intake，让准现场 bag 的可读事实进入 Algorithm、O6 archive/readback 和 O7 consumer/UI，仍不证明真实 production cloud、live Nav2 run 或 delivery success。

## OKR 映射和方向判断

- 当前最低 active Objective：O6、O7，均约 56%。
- 方向判断：继续推进 O6/O7，且本轮从“wrapper readiness”切到“消费现场/准现场 route_bag 材料”。
- O6 对齐：增强任务记录和事件/证据存档，支持同一 `task_id` 回读 `route_bag_evidence`。
- O7 对齐：PC 端运营调试平台可以在历史任务详情和回放入口看到 route bag 是否存在、哪些 topic/message 摘要可读、哪些证据仍不足。
- KR 归档判断：本轮计划阶段不归档 KR。后续即使工程实现完成，也只能在证据达到真实生产云、真实路线回放或真实送达闭环标准后再归档。

## 上轮未完成项

- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/final.md`：下一轮建议优先安排能产出 `route_bag`、live Nav2 pose progress、真实或准现场 Nav2 result、媒体可访问证据或 delivery record 的 sprint。
- `sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/final.md`：下一轮建议优先接真实或准现场 delivery record、operator confirmation、`route_bag` 或 live Nav2 pose progress。
- O6/O7 当前仍未证明真实 production cloud、真实 `route_bag` 已被消费、真实 live Nav2 run、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN 或真实 annotation API/export。

## 本轮核心抓手

本轮选择 `route_bag_evidence` intake。Algorithm 从已有现场/准现场 bag DB3 和 metadata 中提取脱敏摘要，O6 作为 additive evidence 归档和回读，O7 只读展示。

可用输入材料：

- `/Users/m1/apps/rober/sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/no_motion_sensor_20260609_235445/no_motion_sensor_20260609_235445/route_bag/route_bag_0.db3`
- `/Users/m1/apps/rober/sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/pulled_remote_run/field_full_stack_20260609_230304/route_bag/route_bag_0.db3`

这些材料只作为准现场 route bag evidence source。输出必须脱敏，只能包含 source label、basename、size/hash 摘要、topic/message/timestamp 统计、blocked reasons 和 next required evidence，不回显绝对路径、token、raw payload、base64、完整 bag 内容或控制成功声明。

## 最近两轮 blocker 扫描

- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/final.md`：完成态；剩余风险是缺真实 `route_bag`、真实 live Nav2 run、真实 NavigateToPose runtime、真实底盘运动和 delivery success。
- `sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/final.md`：完成态；剩余风险是缺真实 `route_bag`、live Nav2 pose progress、delivery record、operator confirmation 和 delivery success。
- 结论：最近两轮不是同一 blocker blocked 消费。本轮不继续包装 local/mock readiness，而是直接消费已存在的准现场 DB3 route bag 材料。

## Owner 和协同

- `robot-algorithm-engineer`：生成 `trashbot.route_bag_evidence.v1` 脱敏摘要，写入 manifest 顶层和 field motion packet。
- `robot-software-engineer`：在 O6 local/mock archive ingest/readback 中接入 `route_bag_evidence`，支持 consumer include 回读。
- `full-stack-software-engineer`：在 O7 consumer detail / UI 中展示 `route_bag_evidence` 只读摘要、blocked reasons、next evidence 和 false safety fields。
- `product-okr-owner`：三方 worker 返回后统一写 `tech-done.md`、`side2side_check.md`、`final.md`，再决定是否保守更新 OKR；工程 owner 不并行写 `tech-done.md`。

## 验收边界

- 必须产出同一 `task_id` 的 Algorithm -> O6 -> O7 `route_bag_evidence` 证据链。
- 必须保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 不连接 production cloud，不启动 ROS2 runtime，不发布 `/cmd_vel`，不下发 Nav2 goal，不执行真实底盘控制。
- 不把 DB3 存在性写成真实 route execution success、live Nav2 success、operator confirmation 或 delivery success。
- 工程完成后必须各自写 `artifacts/<role>_worker_report.md`，Product 收口统一写 sprint 结果文档。
