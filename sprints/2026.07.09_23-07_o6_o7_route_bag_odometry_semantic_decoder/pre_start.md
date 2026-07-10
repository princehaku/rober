# O6/O7 Route Bag Odometry Semantic Decoder Pre-start

## Sprint 类型

sprint_type: epic

启动时间：2026-07-09 23:07 CST。

## 背景

当前 `OKR.md` 4.1 节中最低活跃 Objective 为 O6 与 O7，均约 74%。上一轮 `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/` 已把 route bag DB3 payload 推进到 per topic/type semantic decode matrix，但 `final.md` 明确剩余风险：当前 decoder 仍有限，后续应把 matrix 中的 unsupported/failed 项逐步转为 decoded evidence，而不是继续新增只读 wrapper。

本轮选择 `nav_msgs/msg/Odometry` 作为下一步安全 decoder。项目已有 `route_bag_pose_progress_replay` 对 Odometry 的只读位姿解析，本轮复用该安全摘要，把 Odometry 纳入 `route_bag_semantic_replay` 与 `route_bag_full_semantic_decode_matrix` 的 decoded 覆盖，再通过 O6/O7 验证透传与展示。

## 上轮未完成项与阻塞

- 未完成项：raw ROS message payload 仍不是全量语义回放；上一轮只覆盖 LaserScan、Image、TFMessage。
- 未完成项：真实 production cloud、真实 live Nav2 route execution、真实 delivery record、operator confirmation 与 delivery success 仍未证明。
- 本轮不重复消费真实 production cloud / TLS / 4G / OSS / live Nav2 blocker，而是在当前本地环境中推进一个可验证 decoder 扩展。

## 本轮目标

1. Algorithm：把 `nav_msgs/msg/Odometry` 纳入 route bag semantic decoder 白名单，输出有限、安全的 odometry pose summary。
2. O6：确认 O6 archive/readback/consumer include 对 Odometry matrix item 保持安全归一、透传和 fail-closed。
3. O7：确认 PC/O7 consumer 与 UI 能展示 Odometry decoded matrix item，且不把 ready 外推成 route execution 或 delivery success。

## Owner

- `robot-algorithm-engineer`：decoder 实现与 Algorithm 测试主责。
- `robot-software-engineer`：O6 合同归一与回读验证主责。
- `full-stack-software-engineer`：O7 consumer/UI 展示验证主责。

## 风险边界

- 本轮证据边界为 `software_proof_route_bag_odometry_semantic_decoder_only` 的能力增量说明；底层既有 schema/proof_scope 仍沿用 `route_bag_semantic_replay` 与 `route_bag_full_semantic_decode_matrix`。
- 不证明真实 production cloud、真实 4G/TLS、真实 OSS/CDN、生产 DB/queue 或生产查询容量。
- 不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、operator confirmation、delivery success 或完整路线长期验收。
