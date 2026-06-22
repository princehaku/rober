# 2026-06-23 01:00 本轮进度当前读数摘要

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 新增 `当前读数` 单行，压缩显示当前轮速读数、行程状态、送达状态和键盘状态。
- 轮速未完成时优先显示已读到的 `L/R`，帮助现场区分“没读到”和“读到了但还是 0/0”；行程成功时显示普通行程成功摘要；送达和键盘只显示完成/未满足结论。
- 该摘要只消费页面已有只读 state，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：补充默认首屏、行程成功送达未完成、键盘可使用三类当前读数断言。
- `docs/product/pc_tools_workstation.md`：同步记录该只读摘要。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`；首轮失败原因是普通首屏出现工程词 `证据`，已改为 `当前读数` 后复测通过。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 首屏读数可读性；不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或 PC 键盘连续手控。
- 真实能力仍需要现场 operator 按安全口径显式执行并提供实车证据。
