# O7 Route Replay Labeling MVP Tech Done

## Sprint 类型

- sprint_type: epic
- automation_id: rober-okr
- owner: full-stack-software-engineer
- finish_time: 2026-07-09 06:15 CST
- evidence_boundary: software_proof_local_mock_consumer_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `O7ConsumerRouteReplayMvp` / `O7ConsumerLabelingMvp` 合同。
  - 固定 route replay cursor 只允许本地 `previous_frame` / `next_frame` / `reset_cursor` / `toggle_playing`，且 `playback_available=false`、`safe_to_play=false`、`sends_to_robot=false`。
  - 固定 labeling submit receipt 为 `submit_blocked_fail_closed`，且 `submit_enabled=false`、`rollback_enabled=false`、`dataset_export_available=false`、`real_annotation_api_connected=false`、`cloud_write_executed=false`。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 在 O6 consumer detail 主路径上派生 `route_replay_mvp`，输出同一 `task_id` 的 frame count、current frame、pose/velocity、events timeline、evidence refs、keyframe refs 和本地 cursor contract。
  - 在同一 detail 上派生 `labeling_mvp`，输出 review item、media/evidence ref、current labels、draft labels、label schema、allowed label types 和 fail-closed submit receipt。
  - 扩大危险 true 字段扫描，`submit_available`、`rollback_available`、`dataset_export_available`、`playback_available`、`safe_to_play`、`real_cloud_archive_connected`、`real_annotation_api_connected`、`real_command_api_connected` 等一旦为 true 就 fail-closed。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - Consumer-detail route replay player 优先消费 `route_replay_mvp`，旧 `trajectory.sample_frames` 仅作为兼容 fallback。
  - Consumer-detail labeling primary path 优先消费 `labeling_mvp`，展示当前 review item、media/evidence ref、current/draft labels、schema、allowed types 和 submit fail-closed receipt。
  - 旧 archive fixture route replay / labeling 面板保留为 debug fallback，状态与 consumer detail 主路径隔离。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 server adapter 从 O6 detail 派生 route replay MVP 和 labeling MVP。
  - 断言所有危险字段保持 false，submit receipt 不会变成成功。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 UI 展示 MVP schema/status、frame cursor、keyframe refs、review item、draft label、schema、allowed label types 和 `submit_blocked_fail_closed`。
  - 保留缺 labeling sample 时 `labeling_missing` 的 fail-closed UI 分支。
- `docs/product/pc_tools_workstation.md`
  - 同步 O7/O6 consumer read 集成指导，说明 `route_replay_mvp` / `labeling_mvp` 字段、UI 主路径和 proof boundary。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 同步 O7 consumer detail MVP response schema、危险字段扫描和只读/fail-closed 边界。

## 验证结果

- `cd pc-tools/workstation && npm run test -- catalog.test.ts`
  - 通过：`Test Files 1 passed (1)`，`Tests 201 passed (201)`，`Duration 47.17s`。
- `cd pc-tools/workstation && npm run test -- App.test.ts`
  - 通过：`Test Files 1 passed (1)`，`Tests 247 passed (247)`，`Duration 29.40s`。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
  - 仅保留既有 Vite 提示：`Some chunks are larger than 500 kB after minification`。
- `cd pc-tools/workstation && npm run lint`
  - 通过：`eslint .` 无报错。
- `git diff --check`
  - 通过：无输出。

## 失败定位和修复

- 首次 `App.test.ts` 失败 1 个用例：`blocks consumer-detail labeling queue primary path when labeling samples are missing`。
- 根因：新增 UI 优先读取 `route_replay_mvp` 后，旧 test fixture 没有该字段，`routeReplayFrames` 的 optional chain 少了一层，`resetRouteReplayCursor()` 触发异常，导致 UI 显示 `consumer_task_detail_api_unavailable` 而不是原本的 `labeling_missing`。
- 修复：`routeReplayFrames` 改为 `consumerTaskDetailResult.value?.route_replay_mvp?.trajectory.sample_frames ?? consumerTaskDetailResult.value?.trajectory.sample_frames`，保留旧 detail fallback。
- 复验：`App.test.ts` 重跑 247 passed。

## 剩余风险

- 本轮仍是 `software_proof_local_mock_consumer_only`，不证明真实生产云、真实 DB/queue、OSS/CDN、TLS/4G、真实机器人数据或真实送达。
- Route replay 只证明 PC 能消费 O6 detail 的安全摘要和浏览器本地 cursor；不证明真实地图叠加、真实关键帧媒体可访问、真实逐帧播放或机器人运动。
- Labeling 只证明 PC 能展示 review/draft/schema/receipt；真实 annotation submit、rollback、autosave、dataset export 和审计日志仍未接通。
- 真实 RTC/视频、ASR/TTS、wheel raw 非零、电梯状态链和完整路线长期验收仍是 O7 后续缺口。
