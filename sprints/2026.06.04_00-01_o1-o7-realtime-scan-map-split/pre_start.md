# O1/O7 Realtime Scan Map Split Pre Start

## sprint_type

epic

## 背景

PC 右侧 live 面板当前把 `雷达未接入 / 等待建图` 合在一个卡片里展示，且后端 `lidar_radar.scan_status` 固定为 `not_proven`。这会把三种状态混在一起：

- LiDAR raw packet 材料可见，但只能说明串口原始包/解析材料，不等于实时雷达。
- ROS2 `/scan` 还未证明，所以按 CEO 口径不能显示“实时雷达已接入”。
- SLAM/map 依赖 `/scan`、TF 和建图链路，必须和 `/scan` 状态拆开展示。

## 本轮目标

把 PC live panel 拆成两个明确区块：

1. `实时雷达 (/scan)`：只认真实 ROS2 `/scan` once/hz 证据。
2. `实时图 (SLAM/map)`：只展示 map/SLAM 是否可用；没有 `/scan` 时等待雷达，有 `/scan` 但无 map 时等待建图。

Raw packet proof 继续保留为工程诊断材料，但不参与主状态灯或“实时雷达 ready”判定。

## Owner

- User Touchpoint Full-Stack Engineer：PC workstation API/UI/type/test/docs。
- Robot Platform Engineer：上位机 `/scan` proof/runtime 状态摘要与 smoke/collector 验证。
- Hardware Infra Engineer：只读复核 LiDAR vendor 来源、串口/baud/start/stop/topic/frame 边界，不做硬件配置改动。

## 风险边界

- 不启用 mock scan 来伪装实时雷达。
- 不改 WAVE ROVER `/dev/ttyS5` 底盘控制链路。
- 不把 raw packet observed 写成 `/scan` observed。
- 不把 PC UI 状态展示写成 HIL、ACK、`safe_to_control=true` 或 delivery success。

## 最近 blocker 复核

近期 O1 LiDAR blocker 仍是 ROS2 Humble runtime / onboard install / `/scan` proof 未闭环。本轮继续推进同一最低 Objective，但目标不是重复消费 blocker，而是把 blocker 机器可读地拆成 `/scan` 与 map 两个用户可见层，并准备 runtime/smoke 验收入口。
