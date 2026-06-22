# 2026-06-23 02:05 键盘验证必须成功转发

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `keyboardVerifiedPulseCount`，`PC 键盘连续手控` 只在固定 manual pulse 返回 `command_forwarded` 且远端 HTTP 为 2xx 后才算已验证。
- 原先的 `keyboardLastDirection != not_loaded` 只代表发生过按键，现在不再作为验收依据。
- manual pulse 被拒绝、远端非 2xx 或 fetch 失败时，清理键盘循环，不再保持 `手控中`，普通首屏显示 `键盘手控请求未成功，未记为已验证。`
- 成功路径仍保持原有边界：键盘 pulse 复用 `POST /api/robot-control/base/manual`，继续受 checklist、operator material 和 bounded pulse 合同约束。
- `pc-tools/workstation/test/App.test.ts`：新增 manual pulse 被拒绝的回归测试，确认按键后仍显示 `键盘手控待验证`，高级 checklist 不 ready，且不会额外发送 stop。
- `docs/product/pc_tools_workstation.md`：同步记录键盘验收必须来自成功转发的 pulse。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`128 passed (128)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只收紧 PC 端键盘验收口径；不证明真实 PC 键盘连续手控已经现场完成。
- 当前真实上位机 operator report 仍是 delivery draft，manual gate 不满足，不能在本轮无现场确认下发 keyboard pulse。
- 真实键盘验收仍需要现场补齐 gate 后，显式启用键盘并按住方向键，让 manual pulse 成功转发。
