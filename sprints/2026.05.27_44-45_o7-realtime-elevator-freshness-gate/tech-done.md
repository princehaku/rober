# 2026.05.27_44-45_o7-realtime-elevator-freshness-gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 `O7RealtimeElevatorProbeResponse` 增加 PC-only freshness gate 字段，且 `latency_lt_2s_proven` 固定为 `false`。
- `pc-tools/workstation/src/server/o7RealtimeElevatorProbe.ts`：probe 成功和 fail-closed 路径均返回观察时间、远端 pose timestamp、pose age、freshness gate status；age 只来自远端 `pose_freshness.age_ms` 或 `robot_pose.timestamp_ms` 派生，不升级为通过。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`：Realtime/elevator cloud probe 和 Realtime map pose preview 附近展示 freshness gate 字段。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：覆盖 UI 和后端 probe freshness gate 字段。
- `docs/interfaces/o7_realtime_elevator_probe_api.md`、`docs/product/pc_tools_workstation.md`：同步说明这些字段是 PC-only freshness gate，不证明真实 ROS2 `/tf`、真实 realtime API 或 <2s 延迟。

## 验证结果

- `cd pc-tools/workstation && npm run test -- --runInBand`：失败于 Vitest 参数不兼容，输出 `CACError: Unknown option --runInBand`，按任务要求改跑不带该参数的测试命令。
- `cd pc-tools/workstation && npm run test`：通过，`Test Files 2 passed (2)`，`Tests 40 passed (40)`。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，Vite 输出 `built in 2.25s`。
- `cd pc-tools/workstation && npm run lint`：通过，ESLint 无输出错误。
- `git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7RealtimeElevatorProbe.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_realtime_elevator_probe_api.md docs/product/pc_tools_workstation.md sprints/2026.05.27_44-45_o7-realtime-elevator-freshness-gate`：通过，无 whitespace error。

## 剩余风险

- 当前改动仍是 PC workstation software proof；未连接真实 ROS2 `/tf`、真实 realtime API、电梯状态链、云端生产链路或机器人控制。
- `remote_pose_age_ms` 只是观察摘要；不能作为 O7-KR1 `<2s` 刷新延迟验收通过证据。
