# O7 Route Replay Labeling MVP PRD

## 用户价值和产品北极星

用户价值：PC 工作站需要把 O6/field evidence 的 detail 从“能读到 wrapper”升级为“能复盘一条历史路线并准备标注”。运营/开发者应能围绕一个 `task_id` 看到 trajectory frames、events、evidence refs、label drafts 和 submit/fail-closed 状态，判断这条任务材料是否能进入训练数据整理。

产品北极星：让小车最终可验证地完成垃圾投递。本 sprint 不直接提升送达能力，而是补齐送达前后的历史证据复盘和训练数据入口，为后续真实路线、关键帧和标注闭环提供 PC 侧工作台。

## OKR 映射和方向判断

- 当前最低未归档 Objective：O7，约 31%。
- 本 sprint 直接针对 O7。
- 方向判断：继续。理由是 O7 已证明 consumer adapter 可消费 O6 `field_evidence` wrapper，但 KR3/KR4 仍缺真实工作台闭环；本轮不需要真实硬件或生产云即可推进软件侧最小可用能力。
- 不调整 O5/O6/O1 方向；O6 只作为 detail 数据输入依赖。

## KR 拆解、更新或历史归档

- O7 KR3 历史路线回放：
  - 输入：O6 consumer detail 或本地等价 mock。
  - 必须展示：`task_id`、frame count、当前 frame、位姿/速度摘要、events timeline、evidence/keyframe refs。
  - 必须支持：只改浏览器或 PC 本地状态的 cursor 操作，不调用机器人控制 API。
- O7 KR4 数据标注/打标界面：
  - 输入：consumer detail 的 labeling/evidence/events/trajectory 白名单摘要，或本地等价 mock。
  - 必须展示：review item、media/evidence ref、current labels、draft labels、label schema/allowed types 摘要。
  - submit 真实 API 不可用时必须有 fail-closed 状态或 receipt，不得显示为提交成功。
- 已完成 KR 历史归档：本轮 planning 阶段无归档。实现验收通过后，若只是 local/mock MVP，仍只能记录为 O7 KR3/KR4 子能力推进，不能把 KR3/KR4 标为完成。

## 本轮核心抓手

核心抓手是 `O7FixturePreviewPanel.vue` 的 O6 consumer read 主路径，而不是旧的纯本地 archive fixture fallback：

- 让用户先加载 consumer task list/detail。
- 选中 task 后进入 route replay 和 labeling 两个最小工作区。
- route replay 与 labeling 共用同一个 `task_id` 和 detail 来源，避免重复读不同 fixture 造成证据断裂。
- 所有状态都可由 Vitest 断言，避免只做视觉文案。

## 需要做什么

后续 full-stack owner 需要交付：

1. consumer detail 到 route replay preview 的最小 server/client contract。
2. consumer detail 到 labeling preview/draft/fail-closed receipt 的最小 server/client contract。
3. shared contracts 类型更新，固定危险字段为 false。
4. `O7FixturePreviewPanel.vue` 中的最小 UI：task selector、route frame cursor、events/evidence refs、label draft/receipt/fail-closed 区块。
5. `catalog.test.ts` 覆盖 server contract、fail-closed 和危险 true 字段。
6. `App.test.ts` 覆盖 UI 渲染、cursor 操作、label draft/status 和 no-control 边界。
7. 更新 `docs/product/pc_tools_workstation.md` 和 O7/O6 接口文档，说明本轮新状态与边界。
8. 更新本 sprint `tech-done.md`，记录实际改动、验证结果和剩余风险。

## 优先级和验收口径

优先级：

1. P0：consumer detail 主路径可生成 route replay + labeling MVP contract。
2. P0：UI 可围绕同一 `task_id` 展示 frame/events/evidence/label drafts 或 fail-closed receipt。
3. P0：危险字段固定关闭：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
4. P1：旧 fixture fallback 保持可用但降级为 debug fallback，不能覆盖 consumer detail 主路径。
5. P1：文档同步说明 proof boundary 和剩余风险。

验收口径：

- `catalog.test.ts` 必须证明有合法 detail/mock 时能输出 task、trajectory frames、events/evidence refs、label drafts/status。
- `catalog.test.ts` 必须证明缺 detail、bad schema、危险 true 字段、submit/control/success claim 会 fail closed。
- `App.test.ts` 必须证明 UI 展示 route cursor、event/evidence refs、label draft/status，并且不会出现真实 submit/control/success 行为。
- build、lint、`git diff --check` 必须通过。

## 对应责任 Engineer

- primary owner：full-stack-software-engineer
- Product Owner 后续只做验收证据核对、OKR 判断、side2side/final 收口和必要 OKR 更新。

## 风险、阻塞和证据链缺口

- 本轮仍可能只形成 `software_proof_local_mock_consumer_only`，不证明生产云、真实 OSS/CDN、TLS/4G、真实机器人数据或真实送达。
- 如果 O6 consumer detail 当前字段不足，full-stack 可在 PC 侧用等价本地 mock 补最小合同，但必须保留切换到真实 O6 detail 的入口和 fail-closed 状态。
- submit receipt 可先是 fail-closed receipt，不要求真实 annotation API；不得把 fail-closed receipt 写成提交成功。
- 真实 RTC/视频、ASR/TTS、wheel raw 非零、真实电梯状态链和完整路线长期验收仍是 O7 后续缺口。

## Sprint 文档

- 已创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 待 full-stack 实现后更新：`tech-done.md`。
- 待验收后更新：`side2side_check.md`、`final.md`。
