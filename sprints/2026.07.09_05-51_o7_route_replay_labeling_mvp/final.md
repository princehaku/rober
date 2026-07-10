# O7 Route Replay Labeling MVP Final

- sprint_type: epic
- close_time: 2026-07-09 06:19 CST
- product_owner: product-okr-owner
- primary_engineer: full-stack-software-engineer
- target_objective: O7 PC 端运营调试与数据训练平台
- target_krs: O7 KR3 历史路线回放、O7 KR4 数据标注/打标界面
- evidence_boundary: software_proof_local_mock_consumer_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 用户价值和产品北极星

本轮把 O7 从“能消费 O6 field evidence wrapper”推进到“同一个 `task_id` 下有 route replay MVP 与 labeling MVP”。PC 工作站现在可以在 consumer detail 主路径看到 trajectory frame count、current frame、pose/velocity、events timeline、evidence/keyframe refs、review item、media/evidence ref、current/draft labels、label schema、allowed types 和 `submit_blocked_fail_closed` receipt。

产品北极星仍是普通用户可验证地完成垃圾投递。本 sprint 只完成运营复盘与数据训练入口的软件侧最小闭环，不代表真实投递、真实控制、真实生产云或真实机器人动作闭环。

## OKR 映射和方向判断

方向判断：继续 O7，下一轮必须优先接真实 route artifacts、真实媒体可访问性或 annotation submit/export 的最小链路，避免继续只产出 surface/review/handoff。

- O7 从约 31% 保守上调到约 34%。本轮新增的事实是 consumer detail 主路径已能派生并展示 route replay / labeling MVP，且 test/build/lint/diff-check 通过。
- O7 KR3 不标完成。当前只证明安全摘要和本地 cursor，不证明真实云端历史任务、真实地图叠加、真实关键帧媒体、真实逐帧播放、机器人运动或长期路线验收。
- O7 KR4 不标完成。当前只证明 review/draft/schema/receipt 展示和 submit fail-closed，不证明真实标注提交、回滚、自动保存、训练集导出或审计日志。
- O6 不上调。本轮只消费 O6 detail，没有新增 O6 archive 写入、生产 DB/queue、OSS、TLS/4G 或真实机器人数据证据。
- O5/O1/O2/O3/O4 不调整。

## KR 拆解和历史归档

- O7 KR3：从 wrapper 展示推进到 `route_replay_mvp` 软件侧 MVP，覆盖 trajectory、events、evidence/keyframe refs 和本地 cursor contract。
- O7 KR4：从旧 fixture preview 推进到 `labeling_mvp` 软件侧 MVP，覆盖 review item、labels、schema、allowed types 和 fail-closed submit receipt。
- 已完成 KR 历史归档：无。本轮是 O7 KR3/KR4 子能力推进，不足以把任何 KR 移入历史完成区。
- 历史记录位置：本轮证据已写入 `docs/process/okr_progress_log.md` 的 `2026-07-09 05-51｜o7_route_replay_labeling_mvp` 条目。

## 本轮核心抓手

核心抓手是让 PC `O7FixturePreviewPanel` 的 consumer detail 主路径直接承载 O7 KR3/KR4 的最小工作台，而不是继续把旧 archive fixture 当作主路径。旧 route replay / labeling 面板保留为 debug fallback，不覆盖 consumer detail 派生的主路径。

## 验收证据

本收口任务不重新运行 full-stack 验收命令，引用 `tech-done.md` 的结果：

- `cd pc-tools/workstation && npm run test -- catalog.test.ts`：`Tests 201 passed (201)`。
- `cd pc-tools/workstation && npm run test -- App.test.ts`：`Tests 247 passed (247)`。
- `cd pc-tools/workstation && npm run build`：通过，仅 Vite chunk warning。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check`：通过，无输出。

首次 `App.test.ts` 有 1 个失败，定位为旧 fixture 缺 `route_replay_mvp` 时 optional chain 少一层。full-stack worker 已修复并复验通过。

## 需要做什么

下一步应优先选择一个能产生真实证据链的 O7/O6/O3 联动小切片：

1. 接入真实 `route.csv`、replay JSONL、keyframe 或 rosbag 到 O6 consumer detail，再由 O7 route replay MVP 消费。
2. 补真实 keyframe/media ref 可访问性 smoke，验证 PC 不是只展示 ref 字符串。
3. 推进 annotation submit/export 的最小后端合同，保持默认 fail-closed，直到有真实写入证据。

## 责任 Engineer

- `full-stack-software-engineer`：负责 PC route replay / labeling 后续真实 API、媒体可访问性和 annotation submit/export。
- `robot-software-engineer`：负责 O6 consumer detail 的真实 artifact seed 和 relay 接入。
- `robot-algorithm-engineer`：负责路线、关键帧、replay JSONL 或 rosbag 的真实数据材料。

## 风险、阻塞和证据链缺口

- 真实 RTC/视频、ASR/TTS、wheel raw 非零、真实电梯状态链和完整路线长期验收仍缺。
- 真实生产云、DB/queue、OSS/CDN、TLS/4G、真实隧道和真实机器人数据仍缺。
- 真实关键帧媒体可访问性、annotation submit、rollback、autosave、dataset export 和审计日志仍缺。
- 所有危险字段继续保持 false：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## Sprint 文档和收口结论

- 已补齐 `side2side_check.md` 和本 `final.md`。
- 已保守更新 `OKR.md`：O7 从约 31% 上调到约 34%，O7 KR3/KR4 不标完成。
- 已更新 `docs/process/okr_progress_log.md`，记录本轮历史进度证据。
- 收口结论：验收通过，边界为 `software_proof_local_mock_consumer_only`。
