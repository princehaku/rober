# O6/O7 Route Bag Full Semantic Decode Matrix Pre Start

## Sprint 类型

sprint_type: epic

启动时间：2026-07-09 22:05 CST。

## 上轮结论

上一轮 `sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/` 已完成 `route_execution_result_delivery_readiness` 的 Algorithm -> O6 -> O7 software proof。O6/O7 进度保守更新到约 71%，但 `final.md` 明确仍缺真实 production cloud、真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation、真实 delivery success，以及 raw ROS message payload 全量语义解码。

## Blocker 复核

- 最近两轮没有把本轮目标 blocked 在同一根因上；上一轮是 software proof 结果链完成，不是外部 blocker。
- 本轮不继续消费真实硬件、4G/TLS、OSS/CDN 或 production DB/queue 缺口。
- 本轮选择现有 DB3 route bag 的离线只读语义解码覆盖矩阵，能在当前 macOS/Python/Node 本地环境中推进。

## 本轮目标

把 O6/O7 从现有 `route_bag_semantic_replay` 的有限白名单摘要推进到 `route_bag_full_semantic_decode_matrix`：

- Algorithm：按 topic/type 输出 DB3 payload 语义解码覆盖矩阵，区分 decoded、unsupported、failed、unsafe，并继续只保留 safe summary。
- O6：接入 archive detail、field evidence、artifact bundle、consumer detail 和 `include=route_bag_full_semantic_decode_matrix`。
- O7：在 consumer detail / artifact bundle readiness / UI 中展示覆盖矩阵、unsupported types、失败原因和 false safety fields。

## Owner

- `robot-algorithm-engineer`：route bag DB3 decode matrix 生成与算法文档。
- `robot-software-engineer`：O6 archive/readback/include 主链路。
- `full-stack-software-engineer`：O7 consumer adapter、共享合同、UI 和产品文档。

## 验收口径

- 同一 `task_id` 的 `route_bag_full_semantic_decode_matrix` 在 Algorithm manifest 顶层和 `field_motion_evidence_packet` 中出现。
- O6 能通过 field-evidence / artifact-bundle ingest 读回，并支持独立 include。
- O7 能展示 matrix readiness，不把 unsupported/failed 解码误读成成功路线执行。
- 全链路固定保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`。

## 风险边界

本 sprint 只证明离线 DB3 payload 语义解码覆盖能力和 O6/O7 readback/display 能力；不证明真实 production cloud、真实 live Nav2 route execution、真实机器人运动、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN 或真实 annotation API/export。
