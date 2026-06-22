# 2026-06-22 18:55 Delivery Draft Auto Gap Check

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏保存送达草稿成功后，自动执行一次 `POST /api/robot-control/delivery/check` 的 confirm=false 缺口复算；保存失败时仍只刷新 latest/summary。
- `pc-tools/workstation/test/App.test.ts`：补充断言，确认保存草稿后 delivery/check 调用次数增加 1，且仍不调用 delivery complete、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录自动复算只刷新缺口，不确认送达、不发车。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只减少保存草稿后的手动复查步骤；真实 delivery success 仍需要现场人员逐项确认后显式提交。
- 当前 wheel raw L/R 非零仍未由真实上位机证明。
