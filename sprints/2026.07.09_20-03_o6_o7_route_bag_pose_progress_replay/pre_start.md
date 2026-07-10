# O6/O7 Route Bag Pose Progress Replay Pre Start

## Sprint 类型

sprint_type: epic

启动时间：2026-07-09 20:03 CST。

## 背景

当前 `OKR.md` 4.1 节 active Objective 中完成度最低的是 O6 和 O7，均约 65%。上一轮 `route_bag_semantic_replay` 已把准现场 DB3 route bag 的 LaserScan / Image / TF 白名单语义摘要接入 Algorithm -> O6 -> O7，但 `final.md` 明确下一步应优先推进 live Nav2 pose progress / route execution result，而不是继续堆 local/mock wrapper。

本轮选择继续消费同一类准现场 route bag 证据，但抓手从“可读语义摘要”推进到“pose progress replay 摘要”：只从 TF / odom 白名单消息中派生位姿样本数、frame pair、起终点、位移、时间跨度和阻断原因，并保持所有危险字段为 false。

## 上轮未完成项和 blocker 扫描

- 上轮剩余缺口：真实 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN、真实 annotation API/export、raw ROS message payload 全量语义解析。
- 最近两轮未以同一外部 blocker 收口；没有连续 2 轮消费同一硬件、凭证或网络 blocker。
- 本轮不依赖真实硬件、真实 4G、真实 OSS/CDN 或真实 production DB，采用本地/mock/离线 DB3 软件验证推进。

## 本轮目标 Objective

- 主目标：O6 云端核心后端。
- 联动目标：O7 PC 端运营调试平台。

## Owner

- `robot-algorithm-engineer`：生成 `trashbot.route_bag_pose_progress_replay.v1`。
- `robot-software-engineer`：O6 archive / consumer readback 支持 `trashbot.o6.route_bag_pose_progress_replay.v1`。
- `full-stack-software-engineer`：O7 consumer adapter / UI 展示 pose progress replay。
- Product 收口：只做 OKR、sprint 对照和最终总结。

## 验收口径

- Algorithm 输出同一 `task_id` 的 pose progress replay 顶层 section，并嵌入 `field_motion_evidence_packet`。
- O6 能从 field evidence、artifact bundle、archive detail、consumer detail 和 `include=route_bag_pose_progress_replay` 回读脱敏摘要。
- O7 能展示 pose progress replay 的只读摘要、blocked reasons、next required evidence 和 false safety fields。
- 所有链路继续保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## 风险边界

- 本轮只证明 route bag / TF / odom payload 的 pose progress 软件回放，不证明真实 live Nav2 route execution。
- 不证明真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 production cloud、production DB/queue、真实 OSS/CDN 或真实 4G/TLS。
- 如真实 DB3 不含可用位姿 topic，本轮必须输出 `blocked_not_proven` 与下一步证据，而不是伪造进度。
