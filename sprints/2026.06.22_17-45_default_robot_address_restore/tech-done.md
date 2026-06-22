# 2026-06-22 17:45 Default Robot Address Restore

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏在固定默认上位机地址 `http://192.168.1.11:8787` 旁新增 `默认地址` 按钮，用户误清空或改错后可一键恢复。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：修正代理层注释，明确前端可以传固定默认地址，代理层只做校验和规范化。
- `pc-tools/workstation/test/App.test.ts`：锁定默认地址按钮初始禁用、清空后可用、点击恢复输入值且不会自动发起新 fetch。
- `docs/product/pc_tools_workstation.md`：同步记录默认地址恢复按钮的行为边界。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只减少 PC 端小车地址误操作成本；wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 和 PC 键盘连续手控仍需继续现场 HIL 验证。
- 当前真实上位机只读 `/api/base/status` 可读到 `/dev/ttyS5 @ 115200` 的 T1001 反馈、电压约 12.43V，但 wheel raw L/R 仍为 0/0。
