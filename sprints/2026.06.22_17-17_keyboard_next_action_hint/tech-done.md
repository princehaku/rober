# 2026-06-22 17:17 Keyboard Next Action Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `键盘手控` 增加 `下一步` 提示，并同步追加到 `本轮进度 / 键盘手控`，让现场先补一个最关键 gate。
- `pc-tools/workstation/test/App.test.ts`：补充默认缺键盘合同、材料 gate 已满足但合同缺失两种状态下的下一步提示断言，确认仍不会调用 manual。
- `docs/product/pc_tools_workstation.md`：同步记录键盘下一步提示只做普通引导，不自动启用键盘或发送 `/api/base/manual`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 键盘连续手控的缺项引导；真实键盘手控仍需要 wheel raw L/R 非零、LiDAR motion delta、移动前检查和后端 bounded pulse 合同全部满足。
- 真实上位机当前只读底盘反馈仍为 T1001 在线、电压约 12.43V，但 wheel raw L/R 为 0/0。
