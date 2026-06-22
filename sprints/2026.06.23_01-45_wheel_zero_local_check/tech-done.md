# 2026-06-23 01:45 轮速零值本地排查确认

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `轮速记录` 在 L/R=`0/0` 卡点出现时新增 `已检查轮速卡点` 本地按钮。
- 点击后只把本页提示切换为“轮速卡点已检查；请低速重试读取非零 L/R”，并把试动按钮文案切到 `检查后重试读非零 L/R`。
- 该按钮不调用 first-jog、manual、stop、Nav2、delivery complete 或 `/cmd_vel`，不保存 operator report，也不把 wheel raw L/R 非零目标置为完成。
- `pc-tools/workstation/test/App.test.ts`：扩展 L/R=`0/0` first-jog 回归，确认本地排查按钮不新增 fetch 调用，且只改变 UI 提示和下一步文案。
- `docs/product/pc_tools_workstation.md`：同步记录 L/R=`0/0` 本地排障确认的边界。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 L/R=`0/0` 卡点的现场操作引导；不证明 wheel raw L/R 非零。
- 当前上位机只读 `GET /api/base/status` 新鲜 T=1001 仍为 `L/R=0/0`。
- 真实非零 L/R 仍需要现场排查电机使能、供电、模式和空间后，显式执行低速 first-jog 并拿到 during-motion T1001 同帧非零 L/R。
