# 2026-06-23 00:22 普通首屏本轮下一步提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 增加 `本轮下一步` 单行提示，按 `轮速记录 -> 行程执行 -> 送达确认 -> 键盘手控` 顺序选择第一项未完成目标。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：该提示复用现有普通 hint，只做展示，不触发刷新、聚焦、提交、手控、Nav2 或送达确认。
- `pc-tools/workstation/test/App.test.ts`：补充默认首屏和 L/R=0/0 readback 两种回归，确认总下一步优先指向轮速记录，并带出当前 L/R=0/0 提示。
- `docs/product/pc_tools_workstation.md`：同步记录该提示的排序和安全边界。

## 验证结果

- `npm test`：首轮发现默认 fixture 的第一未完成项应为 `行程执行` 而不是 `轮速记录`，修正断言后通过，`2 passed (2)`，`125 passed (125)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 普通首屏的目标导航；真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 和真实 PC 键盘连续手控仍需要现场 operator 在安全确认后继续采集和确认。
- 本轮没有发送任何真实运动控制、Nav2 执行或送达确认请求。
