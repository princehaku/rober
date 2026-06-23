# 2026.06.23 08:50 Focus Keyboard Arm After Recheck

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `复查手控条件` 改为专用 `refreshPlainKeyboardGate` handler。
  - 复查仍只读取 summary、底盘反馈、Nav2 latest 和 delivery latest；刷新后如果键盘 gate 已满足，自动聚焦 `启用键盘（按键才动）`，否则继续聚焦 `复查手控条件`。
  - 不自动启用键盘、不发送 keyboard pulse、不调用 manual、stop、Nav2 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展键盘 ready 回归：点击 `复查手控条件` 后焦点落到 `keyboard-control-arm`，且 `/api/robot-control/base/manual` 调用数不变。
- `docs/product/pc_tools_workstation.md`
  - 同步记录键盘复查后的下一步焦点行为和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 136 passed (136)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - `dist/assets/index-Dvd8x4M4.js 403.65 kB`
- 通过：`git diff --check`
- 已恢复历史 smoke artifact 的 `checked_at` 测试副作用，未纳入本轮提交。

## 剩余风险

- 当前变更只改善 PC 键盘连续手控验证入口的操作衔接；真实连续手控仍必须现场人员显式点击启用并按住方向键/WASD，经固定 manual proxy 产生连续脉冲证据。
- 本轮未执行真实运动、Nav2、delivery complete 或键盘 pulse；真实 wheel raw L/R 非零、完整 Nav2 本轮复验、delivery success 和 PC 键盘连续手控仍需现场证据。
