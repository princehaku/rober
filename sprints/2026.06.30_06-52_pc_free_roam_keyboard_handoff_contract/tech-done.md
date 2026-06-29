# PC 自由移动键盘入口 handoff 合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 为普通首屏“自由移动 / 建图”的 `plain-free-roam-keyboard` 按钮补齐 DOM 验收合同。
  - 新增 `data-main-action-kind`、`data-target-source`、`data-activates-keyboard-panel`、`data-free-roam-motion-source`、`data-sends-motion-when-clicked=false`、`data-sends-motion-when-holding`、固定 manual/stop endpoint、pulse interval/duration、连续 pulse 数和 stop 收口字段。
  - 保持用户界面文案和视觉风格不变；按钮点击仍只启用键盘窗口，不发送运动命令。
- `pc-tools/workstation/test/App.test.ts`
  - 补充默认未勾安全、已可启用、点击启用后的自由移动键盘按钮断言。
  - 覆盖 `await_safety_confirm`、`arm_keyboard_no_motion` 和 `armed_waiting_for_keydown` 三段 handoff 状态。
- `pc-tools/README.md`
  - 记录自由移动键盘入口的按钮级 handoff 合同和非发车边界。
- `docs/product/pc_tools_workstation.md`
  - 同步普通 PC 工作站产品文档，明确点击启用键盘不发车，按住方向键/WASD 才会发低速 pulse。

## 验证结果

- 已通过目标用例：
  - `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|splits free movement from mapping acceptance when camera and radar are not ready|starts map recording before auto sweep when camera and radar are ready"`
  - 结果：`Test Files 1 passed (1)`，`Tests 3 passed | 216 skipped (219)`。
- 已通过全量工作站测试：
  - `npm test -- --run`
  - 结果：`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 已通过生产构建：
  - `npm run build`
  - 结果：`vite build` 成功，新 bundle 为 `dist/assets/index-DAEVlU9W.js`。
- 已通过 diff 格式检查：
  - `git diff --check`
  - 结果：无输出，检查通过。
- 已重启 PC Node 工作站：
  - `0.0.0.0:7001` 当前由 `node` 监听，PID `88154`。
  - `curl http://127.0.0.1:7001/` 返回 `index-DAEVlU9W.js` 和 `index-BmaNglvi.css`。

## 剩余风险

- 本轮只做 PC Web DOM 合同和单元测试验证，没有向真实小车发送 manual、free-roam、map、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实 HIL 仍需 CEO 现场确认安全后，再用 7001 页面执行键盘按住、松开 stop、wheel raw L/R 非零和自由移动/建图链路复验。
