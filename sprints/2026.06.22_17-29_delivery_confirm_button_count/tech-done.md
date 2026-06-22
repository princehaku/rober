# 2026-06-22 17:29 Delivery Confirm Button Count

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `最终确认` 的 `确认送达` 按钮在未满足时显示“还差 N 项”，满足后恢复为“确认送达”。
- `pc-tools/workstation/test/App.test.ts`：补充还差 8 项、7 项、1 项和全部满足时的按钮文案断言，确认按钮仍按原 gate 禁用或放开。
- `docs/product/pc_tools_workstation.md`：同步记录按钮文案不放宽送达提交 gate。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 delivery success 最终确认的可读性；真实 delivery success 仍需要现场完成最终确认并由上位机 gate 返回成功。
- 当前真实上位机 delivery latest 仍为 `delivery_success=false`，缺现场最终确认、报告 ready、observed motion/stop 和 delivery_success claim。
