# O7 Route Replay Fixture Preview Tech Done

## Sprint Type

sprint_type: micro

## 实际改动

- 新增 `pc-tools/workstation/src/server/o7RouteReplayPreview.ts`，实现 `trashbot.o7.route_replay_preview.v1` 本地 JSON fixture preview adapter。
- 更新 `pc-tools/workstation/src/shared/contracts.ts`，增加 route replay preview 共享契约，并把 `/api/o7/route-replay-preview?fixtureJson=<local-json>` 纳入 API routes。
- 更新 `pc-tools/workstation/src/server/catalog.ts` 和 `pc-tools/workstation/src/server/index.ts`，挂载只读 API `GET /api/o7/route-replay-preview?fixtureJson=...`。
- 更新 `pc-tools/workstation/test/catalog.test.ts`，覆盖安全 fixture 摘要、缺文件、坏 JSON、unsupported schema、unsafe copy、success claim、control claim 的 fail-closed 行为。
- 更新 `docs/interfaces/o7_realtime_operator_console.md` 和 `docs/product/pc_tools_workstation.md`，明确该能力只是本地 fixture preview，不是 O6 cloud archive、真实历史回放、真实播放控制、真实机器人运动或 O7 完成度提升。

## 验证结果

- `cd pc-tools/workstation && npm run build`
  - 结果：通过。
  - 关键输出：`✓ built in 1.83s`，server TypeScript 编译通过。
- `cd pc-tools/workstation && npm run test`
  - 结果：通过。
  - 关键输出：`Test Files  2 passed (2)`，`Tests  19 passed (19)`。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过，无 lint 输出。

## 失败定位

- 第一轮 `npm run build` 失败于 `src/server/o7RouteReplayPreview.ts` 的 `sampleFrames[0]` 可能为 `undefined`。
- 已修复为显式可选读取 `sampleFrames[0]?.timestamp_ms ?? null`，随后 build/test/lint 均通过。

## 剩余风险

- 该接口只读取本地 fixture 并生成安全摘要，不连接 O6 云端生产归档，不读取 ROS graph，不读取硬件，不发命令。
- `preview_status=fixture_preview_ready` 只代表 JSON 被安全压缩成摘要，不代表真实历史任务列表、真实轨迹 API、真实关键帧归档、真实状态转移时间线、真实逐帧回放、真实机器人控制或真实 delivery success。
- 本轮按要求不修改 `OKR.md`，不提升 O7 百分比。
