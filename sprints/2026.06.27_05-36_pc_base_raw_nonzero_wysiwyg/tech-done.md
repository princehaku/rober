# Tech Done

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 将底盘 feedback samples 的 `latest_nonzero_pair` 提升为 `readback_summary.base.wheel_feedback_latest_nonzero_left_speed/right_speed`。
- 在 `pc-tools/workstation/src/shared/contracts.ts` 同步新增这两个 summary 字段。
- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 更新首屏当前事实和行程证据：Nav2 同窗口反馈仍为 `L/R=0/0` 时，同时展示底盘只读 raw 非零 L/R，而不是只显示 0/0。
- 在 `pc-tools/workstation/test/App.test.ts` 增加回归：Nav2 IMU-only/同窗口 L/R=0/0 但底盘只读 latest_nonzero 为 `164/164` 时，普通首屏显示 raw 非零上下文并继续提示 Nav2 仍需同窗口复验。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run test/App.test.ts`：150 tests passed。
- `npm test -- --run test/catalog.test.ts`：112 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过，包含 `tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json`。
- `git diff --check`：通过。

## 剩余风险

- 该轮只是补齐 PC 所见即所得展示和 summary 字段，不把跨窗口底盘 raw 非零升级为 Nav2 HIL pass。
- 真实完整 Nav2 仍需要在同一执行窗口读到 wheel feedback L/R 非零，delivery success 仍需现场确认。
- 摄像头无首帧和 LiDAR 无 `/scan` 点仍未在本轮解决。
