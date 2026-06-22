# 2026-06-22 17:52 Delivery Next Step Button Labels

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `最终确认` 四个辅助按钮显示当前下一步；勾选后切换为已确认文案。
- `pc-tools/workstation/test/App.test.ts`：覆盖送达辅助按钮从“下一步”到“已确认”的文案变化，并确认这些本地勾选不会新增 fetch。
- `docs/product/pc_tools_workstation.md`：同步记录辅助按钮只改本地 checkbox，不提交 operator report 或 delivery complete。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只降低 delivery success 现场最终确认的漏项成本；真正 delivery success 仍需要现场逐项确认后显式点击 `确认送达` 并通过上位机 gate。
- 当前真实只读状态显示最近 Nav2 目标已 `goal_succeeded`，但 delivery 仍为 false，缺人工确认、观察运动、观察停止和送达 claim。
- 当前真实 `/api/base/status` 仍只读到 T1001 在线、电压约 12.42V，但 wheel raw L/R 为 0/0；PC 键盘连续手控仍未完成真实 HIL 证明。
