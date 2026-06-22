# 2026-06-22 17:37 Keyboard Recheck Button Count

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `复查手控条件` 按钮在键盘 gate 未满足时显示“还差 N 项”，满足后恢复为“复查手控条件”。
- `pc-tools/workstation/test/App.test.ts`：补充默认还差 3 项、只缺键盘入口 1 项、全部满足三种按钮文案断言。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮仍只刷新普通进度，不发送 keyboard pulse、manual、stop 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 键盘连续手控复查入口的可读性；真实连续手控仍依赖 wheel raw L/R 非零、LiDAR motion delta、移动前检查和后端 bounded pulse 合同全部满足。
- 当前真实上位机只读反馈仍显示 wheel raw L/R 为 0/0，键盘手控不能视为完成。
