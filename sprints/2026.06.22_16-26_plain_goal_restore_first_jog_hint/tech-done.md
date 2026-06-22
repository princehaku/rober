# Plain Goal Restore First-Jog Hint

sprint_type: micro

## 实际改动

- 普通首屏“本轮进度”的 `轮速记录` 项在 delivery draft 覆盖 basic safety 时，会提示先点 `恢复试动确认`。
- 提示保留当前 L/R 和 T=1001 帧数，例如 `当前轮速 L/R=0/0，已读到 13 帧，先点恢复试动确认，再试动读非零。`
- 补 Vue 测试覆盖该状态下不调用 `/api/base/manual`，只更新普通进度提示。
- 更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test`，2 个 test files、122 个 tests 全部通过。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改善 PC 普通首屏下一步提示，不发送 first-jog/manual。
- 真实 wheel raw L/R 仍需现场恢复试动确认后运行 first-jog 才能证明非零。
