# PC 键盘启用按钮连续手控合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `keyboard-control-arm` 启用按钮新增按钮级 DOM 合同：主动作类型、目标源、点击不发车、按住才发 pulse、固定 manual/stop 代理、pulse 间隔/时长、当前/最佳连续 pulse 数、验收阈值、同窗口要求、松开后 stop 要求和 stop 收口状态。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖启用前按钮为 `arm_keyboard_no_motion` 且点击不发车。
  - 覆盖启用后按钮为 `armed_waiting_for_keydown`，仍不发车。
  - 覆盖按住方向键时按钮变为 `holding_direction_sends_pulses`，并同步当前 pulse 数。
  - 覆盖连续 2 次 pulse 后，按钮同步显示 `2/2` 连续验收字段。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录启用按钮合同：点击只拿键盘窗口，连续移动必须按住方向键/WASD 并完成 stop 收口。

## 验证结果

- `npm test -- test/App.test.ts -t "enables non-stop motion only after complete operator material and still uses the fixed workstation proxy|keeps keyboard pulses continuous when summary refresh stalls during hold"`：通过，`2 passed | 217 skipped`。
- `npm test -- --run`：通过，`2 passed`，`389 passed`。
- `npm run build`：通过，生成 `dist/assets/index-h0Ats4rs.js` 与 `dist/assets/index-BmaNglvi.css`。
- `git diff --check`：通过，无空白错误。
- 7001 smoke：重启 PC 工作站后，`node` PID `73183` 监听 `*:7001`；`curl -fsS http://127.0.0.1:7001/` 返回当前 `index-h0Ats4rs.js` / `index-BmaNglvi.css`；dist 可检出 `keyboard-control-arm`、`sends-motion-when-holding`、`same-hold-window-required`、`stop-required-after-hold` 和 `stop-settled-after-pulse`。

## 剩余风险

- 本轮只补 PC Web DOM 合同和测试，不触发真实键盘手控、不发送 manual/stop/Nav2/free-roam/delivery 或 `/cmd_vel`。
- 真实键盘连续手控、wheel raw L/R 非零和 stop 收口仍需要现场 HIL 验证。
