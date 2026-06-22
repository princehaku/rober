# 2026-06-22 19:45 Delivery Refs Verified Shortcut

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `最终确认` 区新增 `材料已核对`，只本地勾选“视频和行程材料已核对”。
- `pc-tools/workstation/test/App.test.ts`：补充按钮行为断言，确认安全、到达停稳之后再点击该按钮，缺项从 2 项降到 1 项，并且不会新增任何远程请求。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮不勾选“确认已投放/送达”，也不提交 operator report、delivery complete、manual 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只减少 delivery success 最终确认阶段的重复点击；真实 delivery success 仍需要现场 operator 最后确认已投放/送达，并通过上位机 delivery gate。
- 当前真实上位机只读状态仍显示 operator report 是送达草稿，delivery success 未完成；wheel raw L/R 仍未证明非零。
