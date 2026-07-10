# O6/O7 Route Bag Payload Replay Side2Side Check

## sprint_type: epic

## 对照结果

| 验收项 | 计划口径 | 实际结果 |
| --- | --- | --- |
| Algorithm route bag payload replay | 只读解析 DB3 `messages.data`，输出安全 payload 摘要 | 已完成；`payload_sha256_prefix_samples` 收敛为短 hex `string[]`，并写入 manifest 顶层和 packet |
| O6 archive/readback | 接收 `route_bag_payload_replay` additive 摘要并支持 include 回读 | 已完成；`field_evidence`、`artifact_bundle`、archive task detail、consumer detail 和 `include=route_bag_payload_replay` 均可回读 |
| O7 consumer/UI | 只读展示 source/status、topic/message/timestamp、payload size/hash prefix、blocked reasons、next evidence、false safety fields | 已完成；UI 与测试通过，且未打开 submit/control/action |
| 安全边界 | `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false` | 已保持不变 |
| KR 归档 | 不因 local/mock payload replay proof 归档 KR | 已遵守，本轮未归档任何 KR |

## 用户侧结论

用户现在可以看到同一 `task_id` 下的准现场 DB3 route bag 不仅“存在”，而且其 payload 已经能被安全摘要、被 O6/O7 消费、并能明确指出下一步还缺什么证据。

这仍然不是真实路线执行、真实送达成功或真实 production cloud 证据。

## 现场对照与剩余差距

- 已证明：DB3 payload-derived replay evidence 可消费，topic/message/timestamp 与 payload size/hash prefix 可只读展示。
- 未证明：raw ROS message payload 语义解码、真实 live Nav2 route execution、真实 robot motion、delivery record、operator confirmation、delivery success。
- 未证明：真实 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic、真实 annotation API/export。

## 结论

本轮 side-by-side 对照通过，且与 tech-plan 的最低优先级核对一致：目标就是 O6/O7 的最低项，不是归档 KR。
