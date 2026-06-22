# 2026-06-23 01:20 高级收口键盘需验证

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：默认关闭的高级 `目标收口进度` 中，`PC 键盘连续手控` 不再只因键盘 gate 满足而 ready。
- 现在必须同时满足键盘 gate 且本页发生过方向输入，才显示 ready；gate 满足但未按键时显示 `键盘入口已就绪，仍需按住方向键现场验证`。
- 该改动只调整前端只读收口口径，不自动 arm 键盘、不发送 keyboard pulse、manual、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：更新键盘 ready 流程断言，覆盖按键前高级 checklist false、按键后 true。
- `docs/product/pc_tools_workstation.md`：同步记录高级 checklist 与普通首屏一致的键盘验证口径。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 端键盘验收口径一致性；不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或真实 PC 键盘连续手控。
- 真实键盘连续手控仍需要现场 operator 在材料 gate 满足后显式启用并按住方向键验证。
