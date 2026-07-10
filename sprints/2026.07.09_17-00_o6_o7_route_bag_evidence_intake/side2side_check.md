# O6/O7 Route Bag Evidence Intake Side2Side Check

## Sprint 类型

sprint_type: epic

收口时间：2026-07-09 17:00 CST。

## 对照结论

结论：通过产品侧对照检查。三方 worker 已形成 Algorithm -> O6 -> O7 的 `route_bag_evidence` 证据链，且没有把 DB3 可读摘要声明为真实路线执行或送达成功。

## PRD / Tech Plan 对照

| 验收项 | 实际结果 | 结论 |
| --- | --- | --- |
| Algorithm 生成 `trashbot.route_bag_evidence.v1` | 已在 manifest 顶层和 `field_motion_evidence_packet.route_bag_evidence` 输出 | 通过 |
| 准现场 DB3 摘要可读 | DB3 smoke 输出 `topic_count=3`、`message_count=1473`、sample topics `/tf_static`、`/scan`、`/camera/image_raw`、`contains_abs_path=false` | 通过 |
| Algorithm 测试覆盖 ready / missing / unsafe / safety false | `Ran 26 tests ... OK` | 通过 |
| O6 archive/readback 支持 | field evidence、artifact bundle、archive detail、consumer detail 和 `include=route_bag_evidence` 已接入 | 通过 |
| O6 fail-closed | bad schema、bad proof_scope、dangerous true、path/root/token/raw/base64/credential URL、unsafe topic text 覆盖 | 通过 |
| O6 验证 | `Ran 158 tests in 56.274s OK` | 通过 |
| O7 consumer/UI 展示 | source/status、topic/message/timestamp、blocked reasons、next evidence、false safety fields 已展示 | 通过 |
| O7 验证 | `npm run test` 3 files / `479 passed`，build `built in 1.72s`，lint 通过 | 通过 |
| 安全字段保持 false | `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false` | 通过 |
| 不执行真实控制 | 未连接 production cloud，未启动 ROS2 runtime，未发布 `/cmd_vel`，未下发 Nav2 goal，未执行底盘控制 | 通过 |

## 用户价值检查

本轮价值是让运营人员在 O7 任务详情中看到 route bag 证据摘要，并能从 O6 回读同一 `task_id` 的证据。它减少了“已有路线材料但系统不可见”的断点。

本轮没有达到普通用户可直接验收的真实送达价值，因为没有真实 live route execution、delivery record、operator confirmation 或 delivery success。

## OKR 检查

- O6：可以保守从约 56% 上调到约 59%，因为 archive/read model 已消费准现场 DB3 route bag 摘要。
- O7：可以保守从约 56% 上调到约 59%，因为 PC/O7 已展示 route bag evidence readiness，并通过 `479 passed`、build、lint。
- 不归档 KR：证据边界仍是 `software_proof_route_bag_evidence_intake_only`。
- 方向判断：继续推进 O6/O7，但下一步必须转向 live Nav2 pose progress、raw ROS message payload 解析/回放、delivery record、operator confirmation 和生产云证据。

## 边界声明

本轮不证明：

- 真实 production cloud、真实 4G/TLS、production DB/queue、OSS/CDN live traffic。
- raw ROS message payload、真实 live Nav2 route execution、真实 robot motion。
- 真实 delivery record、operator confirmation、delivery_success=true。
- 真实 annotation API/export、dataset export 或完整路线长期验收。

所有安全字段必须保持 false：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## 需要补齐的证据链

下一步需要补齐：

- live Nav2 pose progress 或可复跑的 raw ROS message payload 解析结果。
- route execution result / failure reason。
- delivery record、operator confirmation 和 dropoff 现场材料。
- production cloud、真实 OSS/CDN、真实 annotation API/export 的链路证据。
