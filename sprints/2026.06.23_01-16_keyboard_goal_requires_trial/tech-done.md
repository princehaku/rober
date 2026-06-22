# 2026-06-23 01:16 键盘目标需现场验证

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 不再把键盘 gate 满足直接显示为 `可使用` 收口。
- 当键盘 gate 已满足但还没有发生过方向输入时，状态显示 `待验证`；若前置轮速、行程和送达都已完成，验收卡点才会提示 `键盘已解锁，点击启用键盘后按住方向键验证。`。
- 发生过键盘方向输入后，状态显示 `已验证`，当前读数显示 `键盘已验证`。
- 该改动只调整前端只读状态口径，不自动 arm 键盘、不发送 keyboard pulse、manual、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：更新键盘 ready 流程断言，覆盖未按键前待验证、按键后已验证。
- `docs/product/pc_tools_workstation.md`：同步记录键盘目标的 stricter ready/verified 区分。

## 验证结果

- `npm test`：首轮失败于测试误把全局验收卡点期望成键盘；实际当前场景行程仍未完成，卡点应继续指向行程。修正断言后通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 首屏对键盘目标的验收口径；不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或真实 PC 键盘连续手控。
- 真实键盘连续手控仍需要现场 operator 在材料 gate 满足后显式启用并按住方向键验证。
