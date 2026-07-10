# O6/O7 DiagnosticArray Semantic Decoder Pre Start

## Sprint 类型

sprint_type: epic

启动时间：2026-07-10 00:06 CST。

## 上轮状态

上一轮 `sprints/2026.07.09_23-07_o6_o7_route_bag_odometry_semantic_decoder/` 已把 `nav_msgs/msg/Odometry` 纳入 route bag semantic replay 和 full semantic decode matrix 的 decoded 覆盖，O6/O7 均收口到约 76%。上轮不是 blocked 收口，但 final 明确留下：matrix 中仍有 unsupported topic type，需要继续补安全 ROS message decoder。

最近两轮 final 均为完成状态，不存在同一 blocker 连续消费。本轮不继续包装 local/mock readiness，而是把一个具体 unsupported ROS type 转成 decoded evidence。

## 本轮目标

最低 active Objective 是 O6/O7（均约 76%）。本轮直接推进 O6/O7：将 `diagnostic_msgs/msg/DiagnosticArray` 从 route bag full semantic decode matrix 的 unsupported 类型推进为安全 decoded 摘要，并通过 O6 readback 与 O7 展示证明同一 `task_id` 可见诊断语义覆盖。

## Owner

- `robot-algorithm-engineer`：实现 DiagnosticArray CDR 安全摘要 decoder，更新算法测试和导航文档。
- `robot-software-engineer`：验证 O6 archive/readback/include 合同保留 DiagnosticArray decoded matrix item，更新接口文档和测试。
- `full-stack-software-engineer`：验证 O7 consumer/UI fixture 展示 DiagnosticArray decoded coverage，更新 PC 文档和前端测试。

## 证据边界

本轮仍是 local/offline software proof。它不证明真实 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN 或真实 annotation API/export。
