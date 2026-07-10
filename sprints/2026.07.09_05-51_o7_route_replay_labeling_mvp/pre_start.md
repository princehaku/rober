# O7 Route Replay Labeling MVP Pre Start

## Sprint 类型

- sprint_type: epic
- automation_id: rober-okr
- start_time: 2026-07-09 05:51 CST
- product_owner: product-okr-owner
- primary_engineer: full-stack-software-engineer
- target_objective: O7 PC 端运营调试与数据训练平台
- target_krs: O7 KR3 历史路线回放、O7 KR4 数据标注/打标界面
- evidence_boundary: software_proof_local_mock_consumer_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 启动背景

`OKR.md` 4.1 当前未归档 Objective 中，O7 约 31%，低于 O6 约 33%、O5 约 80% 和 O1 约 85%，是最低进度 Objective。

上一轮 `sprints/2026.07.09_02-31_o6_field_evidence_archive_ingest/` 已完成 O6 field evidence ingest 与 O7 consumer read adapter 兼容：

- O6 local/mock archive 可写入 `field_evidence` 并通过 consumer list/detail 回读。
- O7 adapter/UI 已能消费 O6 `field_evidence` wrapper。
- 验收边界仍是 `software_proof_local_mock_archive_only`，没有真实路线回放播放器、标注提交闭环、生产云数据流、真实视频或 delivery success。

本轮按自动化记忆要求，停止继续堆叠 wrapper-only surface，直接把 O7 推进到可消费 consumer detail 的历史路线回放和标注工作台最小闭环。

## 用户价值和产品北极星

用户价值：让开发者/运营人员在 PC 工作站里，从 O6/field evidence detail 或本地等价 mock 看到一个可复盘的历史任务：有 `task_id`、轨迹帧、事件、证据引用、标注草稿或明确 fail-closed 状态。这样现场材料不再只停留在 wrapper 摘要，而能进入路线复盘和训练数据准备。

产品北极星保持不变：让普通用户能把垃圾交给小车并可验证地完成投递。本 sprint 只推进运营调试和数据训练平台，不声明真实送达、真实控制、真实生产云或真实硬件闭环。

## OKR 映射和方向判断

- 方向判断：继续 O7，直接针对当前最低进度 Objective。
- O7 KR3：历史路线回放从 wrapper 展示推进到 consumer detail 主路径的 trajectory frames / events / evidence refs 浏览与光标状态。
- O7 KR4：标注/打标界面从本地 fixture 预览推进到 consumer detail 主路径的 review items / label drafts / submit receipt fail-closed 展示。
- O6：作为数据输入依赖，不作为本 sprint 主目标；只消费 O6 consumer read detail 或等价本地 mock。
- 已完成 KR 历史归档：无。本轮计划阶段不归档 KR；只有 full-stack 实现、测试和收口证据成立后，Product Owner 才能判断是否更新 OKR 或历史记录。

## 本轮核心抓手

把 `O7FixturePreviewPanel.vue` 里的 O6 consumer read 主路径做成最小可用闭环：

- 读取 task list/detail，选择 `task_id`。
- 从 detail 提取 trajectory frames、events、evidence refs。
- 提供只读 route replay 光标：上一帧、下一帧、重置、进度或等价状态。
- 展示 labeling draft/queue：review item、media/evidence ref、draft labels。
- 当 submit 真实链路不可用时，展示 fail-closed receipt/status，而不是提供真实提交。

## Owner 和边界

- Product Owner：本轮只创建 planning 文档，并定义验收口径。
- full-stack-software-engineer：后续单线闭环实现、验证、修复并更新 `tech-done.md`。
- 不需要真实硬件、真实 4G、OSS/CDN、真实摄像头恢复或生产云。
- 不允许把 mock replay/labeling 说成真实送达、真实标注提交、生产云闭环或机器人控制。

## 预期留档链路

本 sprint 是 Epic，完整链路为：

1. `pre_start.md`
2. `prd.md`
3. `tech-plan.md`
4. `tech-done.md`（由 full-stack 后续更新）
5. `side2side_check.md`（实现验收后补齐）
6. `final.md`（实现验收后由 Product Owner 收口）
