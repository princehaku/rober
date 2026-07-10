# O6/O7 Route Bag Pose Progress Replay Side2Side Check

## Sprint 类型

sprint_type: epic

检查时间：2026-07-09 20:54 CST。

## 对照结论

本轮目标是把 O6/O7 最低进度项从 route bag semantic replay 推进到 pose progress replay。对照 `tech-plan.md`：

- Algorithm 已产出 `trashbot.route_bag_pose_progress_replay.v1`，并写入 manifest 顶层和 `field_motion_evidence_packet.route_bag_pose_progress_replay`。
- O6 已支持 `trashbot.o6.route_bag_pose_progress_replay.v1`，覆盖 field evidence、artifact bundle、archive detail、consumer detail 和 `include=route_bag_pose_progress_replay`。
- O7 已从多入口归一化并在 PC UI 展示 pose topic types、frame pairs、start/end pose、displacement、nonzero observed、blocked reasons、next evidence 和 false fields。
- 所有危险字段继续为 false：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## OKR 最低优先级核对

tech-plan.md 开工时确认最低 active Objective 是 O6/O7，均约 65%。本轮直接针对 O6/O7，收口后保守更新到约 68%。

本轮不归档 KR。理由：证据仍是 local/mock/software proof，不是生产云、真实 live Nav2、真实机器人运动或真实送达。

## 验证证据

- Algorithm worker report：`Ran 41 tests in 0.192s OK`。
- O6 worker report：`Ran 161 tests in 57.594s OK`。
- O7 worker report：`479 tests passed`，build passed，lint passed。

## 对照风险

- 已满足软件侧 route bag pose progress replay 可读、可归档、可展示。
- 未满足真实 production cloud、真实 live Nav2 route execution、真实 delivery success。
- 下一轮应优先消费真实 live Nav2 route execution result / delivery record / operator confirmation，而不是继续只堆叠 local/mock wrapper。
