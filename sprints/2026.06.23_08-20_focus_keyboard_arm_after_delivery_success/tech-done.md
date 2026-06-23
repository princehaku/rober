# 2026.06.23 08:20 Focus Keyboard Arm After Delivery Success

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - delivery gate 通过后，如果键盘 gate 已满足，普通首屏优先聚焦 `启用键盘（按键才动）`。
  - 如果键盘 gate 仍缺材料，则保持聚焦键盘面板，让现场先看缺项。
  - 聚焦不自动启用键盘、不发送 keyboard pulse、不调用 manual、stop、Nav2 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展最终送达提交成功回归：当键盘 gate 已满足时，焦点落到 `keyboard-control-arm`，按钮可用且仍未发送 manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 delivery success 后优先聚焦键盘启用按钮的安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 135 passed (135)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - `dist/assets/index-AU-X-C4P.js 403.49 kB`
- 通过：`git diff --check`
- 已恢复历史 smoke artifact 的 `checked_at` 测试副作用，未纳入本轮提交。

## 剩余风险

- 当前变更只改善 delivery success 后进入 PC 键盘连续手控验证的操作衔接；真实连续手控仍必须现场人员显式点击启用并按住方向键/WASD，经固定 manual proxy 产生连续脉冲证据。
- 本轮未执行真实运动、Nav2、delivery complete 或键盘 pulse；真实 wheel raw L/R 非零、完整 Nav2 本轮复验、delivery success 和 PC 键盘连续手控仍需现场证据。
