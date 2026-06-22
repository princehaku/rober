# Plain Goal Progress Refresh

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- 在普通 PC 首屏“本轮进度”区域新增 `刷新进度` 按钮。
- 按钮只调用只读刷新链路：PC summary、最近 Nav2 行程执行结果、最近 delivery 状态。
- 补充 Vue/Vitest 用例，确认点击 `刷新进度` 不调用 `/api/robot-control/nav2/goal/execute`、`/api/robot-control/delivery/complete`、`/api/robot-control/base/manual` 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md`，说明普通首屏刷新进度的可用性和安全边界。

## 验证结果

- `npm test`：通过，2 个测试文件、115 个用例。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过。

## 剩余风险

- 本轮是 PC 首屏只读易用性改进，不新增真实底盘、Nav2 或 delivery 动作能力。
- 真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 和 PC 键盘连续手控仍需要现场人员在安全确认后继续采集或确认；本轮没有代替真实 HIL 证据。
