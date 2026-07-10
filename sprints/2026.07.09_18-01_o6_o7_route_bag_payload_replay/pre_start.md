# O6/O7 Route Bag Payload Replay Pre Start

## sprint_type: epic

启动时间：2026-07-09 18:01 CST。

## 用户价值和产品北极星

普通用户最终需要的是“这次任务的路线材料能不能被安全地回放和复盘”，而不是再多一层只读 wrapper。上一轮已经把准现场 DB3 route bag 的元数据摘要接入 O6/O7，本轮要把同一批 bag 从 `metadata/topic/message count` 推进到 `payload-derived replay evidence`：Algorithm 只读解析 `messages.data` BLOB，O6 做 archive/readback/include，O7 做 consumer detail / UI readiness 展示。

产品北极星不变：普通手机用户把垃圾交给机器人后，机器人要可验证地完成垃圾投递。本轮只做安全的 payload 摘要与回放准备，不证明真实 live Nav2 路线执行或送达成功。

## OKR 映射和方向判断

- 当前最低 active Objective：O6、O7，仍并列约 59%。
- 方向判断：继续推进 O6/O7，并从“bag metadata intake”切换到“payload-derived replay evidence”。
- O6 对齐：增强任务记录、事件/证据存档和 include 回读能力，让同一 `task_id` 可消费 payload 摘要与 replay readiness。
- O7 对齐：PC 端运营调试平台要能看见 payload replay readiness、topic payload 大小与 hash 前缀、timestamp sample，以及下一步还缺哪些证据。
- KR 归档判断：本轮计划阶段不归档 KR。即使工程完成，也只能在证据达到真实生产云、真实 live Nav2 route execution、真实 delivery record/operator confirmation 或完整路线验收标准后再归档。

## 上轮完成项和承接点

- `sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/final.md` 已完成 DB3 route bag 元数据摘要 intake。
- 上一轮明确要求下一步优先消费 live Nav2 pose progress 或 raw ROS message payload 解析/回放，而不是继续新增只读 wrapper。
- 本轮承接点：沿用同一 `task_id` 的准现场 DB3 材料，但输出从 metadata 摘要升级为安全 payload-derived replay evidence。

## 本轮核心抓手

本轮选择 `route_bag_payload_replay`。Algorithm 只读读取 DB3 `messages.data` BLOB，计算安全摘要，不输出 raw/base64/content/绝对路径。O6 作为 additive evidence 归档和回读。O7 只读展示 replay readiness，不打开 submit/control/action。

可用输入材料仍然来自上一轮已知准现场 route bag DB3；实现阶段允许工程 owner 在本地以绝对路径读取，但输出与文档必须只保留脱敏 source label、basename、size/hash prefix、topic/message/timestamp 摘要和 blocked reasons，不回显原始 payload 或文件路径。

## 最近两轮 blocker 扫描

- `sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/final.md`：完成态，不是 blocked。主要剩余风险是缺真实 `route_bag`、live Nav2 pose progress、delivery record、operator confirmation 和 delivery success。
- `sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/final.md`：完成态，不是 blocked。主要剩余风险是只证明了 DB3 元数据摘要 intake，没有证明 raw ROS message payload 的安全解析/回放。
- 结论：最近两轮没有同一 blocker 连续消费。本轮直接消费已有 DB3 payload，不继续堆 wrapper。

## Owner 和协同

- `robot-algorithm-engineer`：从 DB3 `messages.data` 只读生成安全 payload 摘要和 replay readiness，写入 manifest 顶层和 packet。
- `robot-software-engineer`：在 O6 archive/readback/include 中接入 payload-derived evidence，保持 fail-closed 和 additive。
- `full-stack-software-engineer`：在 O7 consumer detail / UI 中展示 payload replay readiness、payload size/hash 前缀和 blocked reasons。
- `product-okr-owner`：三方 worker 返回后统一写 `tech-done.md`、`side2side_check.md`、`final.md`，再决定是否保守更新 OKR；工程 owner 不并行写 `tech-done.md`。

## 验收边界

- 必须产出同一 `task_id` 的 Algorithm -> O6 -> O7 `route_bag_payload_replay` 证据链。
- 必须保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 必须只读解析 DB3 `messages.data`，但不能输出 raw/base64/content/绝对路径/凭证信息。
- 不连接 production cloud，不启动 ROS2 runtime，不发布 `/cmd_vel`，不下发 Nav2 goal，不执行真实底盘控制。
- 不把 DB3 payload 可读性写成真实 route execution success、live Nav2 success、operator confirmation 或 delivery success。

