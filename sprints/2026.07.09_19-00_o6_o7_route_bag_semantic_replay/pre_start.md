# O6/O7 Route Bag Semantic Replay Pre-start

## Sprint 类型

sprint_type: epic

启动时间：2026-07-09 19:00 CST。

## 上轮未完成项和本轮接续

上一轮 `sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/` 已把准现场 DB3 route bag 从 metadata 摘要推进到 payload-derived replay evidence，并通过 Algorithm / O6 / O7 的软件验证。

仍未完成的关键缺口：

- `messages.data` 仍只是 payload size/hash prefix 摘要，缺少可供 O6/O7 消费的 ROS topic 语义摘要。
- O6/O7 仍不能回答同一 `task_id` 的 route bag 中是否有可解释的 `/scan`、`/camera/image_raw`、`/tf`/`/tf_static` 样本统计。
- 当前证据仍不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、operator confirmation 或 delivery success。

## Blocker 扫描

最近两轮收口没有主结论 blocked：

- `2026.07.09_18-01_o6_o7_route_bag_payload_replay/final.md`：状态完成，剩余风险是语义解码和真实现场链路未证明。
- `2026.07.09_17-00_o6_o7_route_bag_evidence_intake/final.md`：状态完成，剩余风险是 raw payload / live route / delivery 未证明。

本轮不是重复消费硬件、凭证、OSS/CDN 或公网 blocker，而是继续沿最低进度 O6/O7 做本地/mock 软件 proof。

## 本轮目标

在不启动 ROS2 runtime、不连接真实硬件、不输出 raw payload 的前提下，把 route bag payload replay 推进为 `route_bag_semantic_replay`：

- Algorithm：从 rosbag2 SQLite DB3 的 `topics.type` 与 `messages.data` 中提取白名单 ROS 消息语义摘要。
- O6：归档、回读并 fail-closed 暴露该语义摘要。
- O7：PC consumer detail 展示同一 `task_id` 的语义 replay readiness，继续锁死控制与 delivery success 字段。

## Owner 和并行策略

本 sprint 跨 3 个 owner，接口 contract 已在 `tech-plan.md` 写清，文件范围互不重叠，采用并行子 agent：

- `robot-algorithm-engineer`：Algorithm 语义摘要生成器、算法测试、导航文档。
- `robot-software-engineer`：O6 archive/readback 合同、后端测试、接口文档。
- `full-stack-software-engineer`：O7 consumer adapter/UI/shared contract、前端测试、产品文档。

收口阶段由 `product-okr-owner` 根据三个 worker report 更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 验收口径

- 三个 worker report 必须存在且记录实际改动、验证命令、日志摘要和剩余风险。
- Algorithm / O6 / O7 对 `route_bag_semantic_replay` 的 schema、proof_scope、安全字段、blocked reasons 和 next evidence 一致。
- 所有新增能力保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 本轮只允许声明 `software_proof_route_bag_semantic_replay_only`，不得写成真实 route execution、真实生产云或真实送达成功。
