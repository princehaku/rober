# 2026-06-22 19:25 Delivery Basic Safety Shortcut

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `最终确认` 区新增 `勾选安全三项`，只本地勾选“人在旁边可接管 / 周围安全 / 停止手段就绪”。
- `pc-tools/workstation/test/App.test.ts`：补充按钮行为断言，确认缺项从 7 项降到 4 项，并且不会新增任何远程请求。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮不勾选到达、停止、材料核对或送达成功，也不提交 operator report、delivery complete、manual 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只减少 delivery success 最终确认阶段的重复点击；真实 delivery success 仍需要现场 operator 分别确认到达/移动、停止、材料核对和已投放/送达，并通过上位机 delivery gate。
- 当前真实上位机只读状态仍显示 wheel raw L/R 未非零，delivery success 未完成。
