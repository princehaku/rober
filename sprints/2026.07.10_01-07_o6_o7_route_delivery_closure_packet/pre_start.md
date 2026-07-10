# O6/O7 Route Delivery Closure Packet Pre-Start

## Sprint 类型

sprint_type: epic

启动时间：2026-07-10 01:07 CST。

## 上轮输入

- 最近两轮 `final.md` 均为完成态，未 blocked。
- `sprints/2026.07.09_23-07_o6_o7_route_bag_odometry_semantic_decoder/final.md` 与 `sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/final.md` 连续推进 decoder 覆盖。
- 最新 `OKR.md` 明确要求下一轮优先真实/准现场 live Nav2 result、delivery record/operator confirmation 或 production cloud，避免继续只补 decoder。

## 本轮目标

本轮针对最低 active Objective O6/O7（均约 78%），推进 `route_delivery_closure_packet`：

- Algorithm 把同一 `task_id` 下的 Nav2 goal evidence、delivery result evidence、operator confirmation readiness、route pose progress readiness 收束成闭合包。
- O6 archive/readback 将该闭合包作为 additive 安全摘要进入 detail、field evidence、artifact bundle 和 consumer include。
- O7 consumer/UI 展示闭合包摘要，继续固定 `safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`。

## 不重复消费的 blocker

本轮不继续做 `route_bag_full_semantic_decode_matrix` decoder 覆盖；该方向已连续两轮消费。本轮仍缺真实硬件、真实 production cloud 和真实 delivery success，但可以用本地/准现场 fixture 做软件可验证进展，明确边界为 `software_proof_route_delivery_closure_packet_only`。

## Owner

- Algorithm owner：`robot-algorithm-engineer`
- O6 owner：`robot-software-engineer`
- O7 owner：`full-stack-software-engineer`
- Product closeout：`product-okr-owner`

## 预期证据

- Algorithm 单测证明 ready 与 blocked 两条 closure packet 路径。
- O6 单测证明 field evidence / artifact bundle / consumer include 能读回 closure packet，危险 true 仍 fail-closed。
- O7 测试证明 PC detail 能消费并展示 closure packet，且不会把闭合包误读成真实送达成功。
