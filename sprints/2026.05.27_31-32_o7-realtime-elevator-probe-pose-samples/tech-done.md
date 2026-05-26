# O7 realtime/elevator probe pose and samples

sprint_type: micro

## 实际改动

- 更新 PC workstation realtime/elevator probe contract，新增 `robot_pose_summary` 和 `elevator_state_samples_summary`。
- 更新 `buildO7RealtimeElevatorProbe()`，从远端 `/api/o7/realtime-elevator/snapshot` 白名单提取 robot pose 与最多 5 条电梯状态链 sample 摘要；fail-closed 默认也返回 blocked/not_loaded 值。
- 更新 O7 Previews UI，在 `Probe realtime/elevator snapshot` 结果中展示 robot pose 与 elevator state samples 摘要，同时保留 map ref、map frame、pose freshness、route membership false fields、current floor、human takeover、key false fields 和 dangerous true fields。
- 更新 catalog/UI 测试，覆盖 fixture-backed snapshot 的 pose/sample 摘要提取、危险字段 true 仍 fail-closed，以及 UI 渲染新增字段。
- 更新 `docs/interfaces/o7_realtime_operator_console.md`、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，同步说明新增摘要字段和边界。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。关键输出：`✓ 31 modules transformed.`、`✓ built in 2.12s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  36 passed (36)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 lint 输出。
- `git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7RealtimeElevatorProbe.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_31-32_o7-realtime-elevator-probe-pose-samples`：通过，无 whitespace error 输出。

## 剩余风险

- 本轮只打通 PC probe contract、UI 展示和本地测试；没有打通真实 RTC/视频、真实 ROS2 `/tf`、真实电梯设备、真实楼层识别、真实手控/寻路、机器人 ACK 或硬件 HIL。
- `TRASHBOT_O7_REALTIME_ELEVATOR_SNAPSHOT_JSON` 仍是 cloud relay runtime 的 fixture-backed 输入，不能外推成真实实时地图或真实电梯状态链 connected。
