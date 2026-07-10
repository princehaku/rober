# O6/O7 Route Bag Evidence Intake PRD

## 用户价值

运营人员和后续手机用户需要知道某个任务是否已经有可回放、可排障的路线 bag 材料。当前 O6/O7 已有多层 software proof，但仍缺 `route_bag` 被真实消费后的结构化摘要。本轮把准现场 DB3 bag 从“文件存在”推进成同一 `task_id` 下可归档、可回读、可展示的 `route_bag_evidence`。

## 产品北极星

北极星仍是普通手机用户可验证地完成垃圾投递。`route_bag_evidence` 只是让路线材料进入证据链，帮助回答“这次任务有什么路线采集材料、topic/message 统计是否可读、下一步还缺什么”。它不能替代真实 live Nav2、真实投递记录或用户交付确认。

## OKR 映射和方向判断

- O6 KR2/KR6：任务记录和事件/证据存档继续增强，consumer read 可以围绕同一 `task_id` 回读 `route_bag_evidence`。
- O7 KR3/KR4：PC 历史路线回放和标注工作台能看到 bag readiness、topic/message 摘要、blocked reasons 和 next evidence。
- 方向判断：继续推进 O6/O7，并明确从只读 wrapper 转向消费已有准现场 route bag 材料。
- KR 归档判断：不因本轮 PRD 归档任何 KR。工程完成后若只有 local/mock intake，也仍不归档。

## 需求范围

1. Algorithm route bag evidence 摘要：
   - 输入允许是已有 `route_bag/metadata.yaml` 和 `route_bag_0.db3`。
   - 首选材料为 2026-06-09 两份现场/准现场 route bag DB3。
   - 输出 `trashbot.route_bag_evidence.v1`，proof scope 为 `software_proof_route_bag_evidence_intake_only`。
   - 摘要字段只允许包含安全白名单：schema、proof_scope、source label、task_id、status、metadata/db3 present、db3 readable、db3 size、sha256 prefix、topic count、message count、timestamp range、sample topic names、blocked reasons、next required evidence、false safety fields。
   - 缺文件、DB3 不可读、SQLite schema 缺 `topics/messages`、topic 为空、message 为 0、危险 true、路径/root/token/raw/base64/credential URL 时 fail-closed。

2. O6 archive/readback：
   - `field-evidence` 和 `artifact-bundle` ingest 接收 `route_bag_evidence` additive 摘要。
   - archive task detail、field evidence、artifact bundle、consumer detail 和 `include=route_bag_evidence` 可回读。
   - O6 只保留脱敏摘要，不读取完整 bag payload，不回显绝对路径或原始消息。

3. O7 consumer/UI：
   - consumer adapter 默认请求或读取 `route_bag_evidence`。
   - UI 展示 source/status、topic/message counts、timestamp range、blocked reasons、next evidence 和 false safety fields。
   - route replay / labeling workspace 只能把它作为 readiness support，不打开 submit/control/action。

## 非目标

- 不证明真实 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic。
- 不证明 live Nav2 run、Nav2 result success、真实底盘运动、wheel raw 非零或 route execution success。
- 不证明真实 delivery record、operator confirmation、dropoff completion 或 delivery success。
- 不执行 ROS2 runtime、`/cmd_vel`、Nav2 goal、manual control、keyboard control 或任何硬件动作。
- 不把 DB3 内部消息 payload、绝对路径、token、raw/base64 或完整 artifact 暴露给 O6/O7/UI。

## 验收口径

- Algorithm 单元测试覆盖 ready、missing DB3、unreadable DB3、empty topics/messages、unsafe text 和 safety false。
- O6 单元测试覆盖 field-evidence/artifact-bundle ingest、archive detail、consumer include、missing/unsafe fail-closed。
- O7 测试覆盖 consumer detail 展示、artifact bundle readiness 汇总、UI 文案/DOM、unsafe fail-closed。
- 三个 worker 均写入各自 `artifacts/<role>_worker_report.md`，Product 后续统一收口写 `tech-done.md`。
- 全链路必须保留 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## 优先级

P0：打通 `route_bag_evidence` Algorithm -> O6 -> O7 主链路，并保持 fail-closed。

P1：O7 route replay/readiness 面板展示 topic/message/timestamp 摘要和 next evidence。

P2：后续再接 live Nav2 pose progress、delivery record、operator confirmation 媒体和真实 cloud/OSS 证据。
