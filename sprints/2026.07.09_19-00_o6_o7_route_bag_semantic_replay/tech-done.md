# O6/O7 Route Bag Semantic Replay Tech Done

## Sprint 类型

sprint_type: epic

记录时间：2026-07-09 20:10 CST。

## 实际改动

本轮实际实现由三位 worker 完成，Product 侧据此收口：

- Algorithm：把准现场 DB3 route bag 从 payload 摘要推进到 `route_bag_semantic_replay`，对白名单 ROS topic type 提供有限语义摘要，并继续写入 manifest 顶层与 `field_motion_evidence_packet`。
- O6：新增 `trashbot.o6.route_bag_semantic_replay.v1` readback，允许同一 `task_id` 的 semantic replay 经 field evidence、artifact bundle、archive detail、consumer detail 与 `include=route_bag_semantic_replay` 回读。
- O7：新增 semantic replay consumer/UI 只读展示，覆盖 semantic topic types、LaserScan/Image/TF summary、blocked reasons、next required evidence 和 false safety fields。

本轮 Product 收口文件：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/tech-done.md`
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/side2side_check.md`
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/final.md`

## 验证结果

三侧 worker report 证据：

- Algorithm：`Ran 37 tests in 0.169s`，`OK`。
- O6：`Ran 160 tests in 56.976s`，`OK`。
- O7：`npm run test` 为 `479 passed`，`npm run build` 通过且 `built in 1.74s`，`npm run lint` 通过。

Product 收口继续确认：

- 证据边界统一为 `software_proof_route_bag_semantic_replay_only`。
- 安全字段继续保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- `route_bag_semantic_replay` 已进入 sprint 留档、OKR 快照和详细历史。

## 偏差与修正

- 本轮 sprint 目录原先尚未创建 `tech-done.md`、`side2side_check.md`、`final.md`，Product 收口时已补齐。
- OKR 进度上调保持保守，只把 O6/O7 从约 62% 上调到约 65%，不把 software proof 写成真实现场完成。

## 剩余风险

- 本轮只证明 `software_proof_route_bag_semantic_replay_only`，不证明真实 production cloud、真实 TLS/4G、真实 OSS/CDN、真实 annotation API/export。
- 本轮不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success。
- 本轮新增的是白名单有限语义摘要，不等于 raw ROS message payload 全量语义解码能力。
