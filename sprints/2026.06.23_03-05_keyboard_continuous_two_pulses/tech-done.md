# Keyboard Continuous Two Pulses

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`PC 键盘连续手控` 验收从 1 次成功 keyboard manual pulse 收紧为至少 2 次成功转发；普通首屏和高级目标收口显示 `已成功 N/2 次`。
- `pc-tools/workstation/test/App.test.ts`：键盘手控测试改为第一次成功 pulse 后仍保持待验证，推进一次 keyboard interval 产生第二次成功 pulse 后才显示已验证。
- `docs/product/pc_tools_workstation.md`：同步记录键盘连续手控验收口径和安全边界。

## 验证结果

- 通过：`npm test`，结果 `2 passed (2)`、`130 passed (130)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，结果 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
- 通过：`git diff --check`。

## 剩余风险

- 本轮没有在真实车上按键验证；只是收紧 PC 端验收口径，避免一次 pulse 被误判为连续手控完成。
- 真实上位机当前仍缺 wheel raw L/R 非零、delivery success 和完整现场键盘材料。
