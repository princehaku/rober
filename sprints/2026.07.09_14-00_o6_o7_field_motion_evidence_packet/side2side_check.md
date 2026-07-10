# O6/O7 Field Motion Evidence Packet Side-by-Side Check

## sprint_type: epic

## 计划对照结果

1. 计划要求消费已有 6 月现场材料，而不是继续新增 wrapper：
   - 已满足。packet 直接引用 `map.yaml/.pgm`、`route.csv`、keyframes、remote_capture motion logs，并生成 `derived_replay.jsonl`。
2. 计划要求把 `route_bag_or_live_nav2_log` 定义为可选增强证据：
   - 已满足。manifest 内 `route_bag_or_live_nav2_log.present=true`，`source=live_motion_log`，`route_bag_present=false`。
3. 计划要求 O6 ingest/readback 消费同一 packet：
   - 已满足。O6 支持 field evidence manifest / artifact bundle 中的 `field_motion_evidence_packet` additive ingest/readback。
4. 计划要求 O7 replay / labeling workspace 消费同一 packet 摘要：
   - 已满足。O7 consumer detail、artifact bundle readiness、route replay、labeling workspace 已消费 packet，且对危险输入 fail-closed。
5. 计划要求所有控制类字段保持 false：
   - 已满足。`safe_to_control: false`、`delivery_success: false`、`primary_actions_enabled: false`、`robot_control_executed: false`。

## 用户价值对照

- 对 O6：同一 `task_id` 的现场运动材料现在可以作为更接近真实路线证据的 archive payload，而不再只是 local/mock wrapper 叠加。
- 对 O7：PC 工作站现在可以围绕同一 packet 判断路线回放、标注和 bundle readiness 的证据是否足够，而不是只看孤立摘要。
- 对产品北极星：这是“可验证地送垃圾”所需的现场运动证据链补全，不是送达闭环完成。

## 证据边界复核

- 本轮只证明 `software_proof_field_motion_evidence_packet_only`。
- 不证明真实 production cloud、真实 `route_bag`、真实 Nav2 live run、真实 delivery success。
- 不证明真实 OSS/CDN、真实 annotation API/export、真实媒体访问。

## 验收判断

- 本 sprint 作为 O6/O7 产品收口通过。
- O6/O7 可保守上调到约 `50%`。
- KR 不归档，仍留在当前推进区。
