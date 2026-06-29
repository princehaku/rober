# PC Nav2 执行 runtime 证据 readback

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`/api/robot-control/nav2/goal/execution/latest` 从最近一次 O11 execution artifact 提升 `readback_publishes_cmd_vel` 和 managed runtime requested/started/lifecycle ready/cleanup 字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：`/api/robot-control/summary.readback_summary.nav2` 同步暴露 `goal_execution_readback_publishes_cmd_vel`、`goal_execution_managed_runtime_*`，用于判断自动驾驶执行链路卡在 Nav2、bridge 还是底盘反馈。
- `pc-tools/workstation/src/shared/contracts.ts` 和 `RobotControlConsolePanel.vue`：更新合同和前端 Nav2 证据表数据源，让普通 PC 页面可直接展示这些只读证据。
- `pc-tools/workstation/test/catalog.test.ts`：补 live 形状回归，覆盖旧 PWM 执行成功但 wheel raw L/R 仍为 0/0 时，summary 必须暴露下次 ROS、runtime 和 `/cmd_vel` readback。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`：同步说明本轮只读证据提升和边界。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm test -- test/catalog.test.ts`：通过，168 tests OK。

## 剩余风险

- 本轮没有执行真实 Nav2 goal，也没有发送 `/cmd_vel` 或底盘 manual 命令；自动驾驶“车是否实际移动”仍需要现场勾选安全确认后重跑图上路线，并检查本轮新增字段与 wheel raw L/R 是否闭合。
- 相机当前仍是 DV20 UVC 无首帧，不是页面独占；该问题不阻塞低速移动或 Nav2 重跑，但阻塞建图验收。
- 当前工作区已有两份历史 DOM smoke artifact 是改动状态，本轮未触碰、未纳入验证或提交。
