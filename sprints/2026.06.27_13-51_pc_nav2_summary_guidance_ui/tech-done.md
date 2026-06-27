# PC Nav2 summary guidance UI consumption

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏事实条、行程进度、行程摘要和本轮进度下一步优先消费 `safe_command_boundary.nav2_goal_next_action`。
  - 当 summary 明确 `nav2_goal_wheel_feedback_status=goal_succeeded_but_wheel_lr_zero` 时，界面直接提示“勾选行程前安全确认后用 ROS 重跑图上路线”，避免把上次 `pwm` action success 误读成完整行程。
- `pc-tools/workstation/test/App.test.ts`
  - 在 IMU-only / wheel raw L/R=0/0 回归用例里补充 summary guidance 字段，并断言普通用户卡片展示 ROS 重跑动作。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC 普通首屏开始消费 `nav2_goal_next_action` 的产品边界。

## 验证结果

- `npm test -- --run App.test.ts -t "IMU-only route arrival"`
  - 结果：通过，`1 passed | 164 skipped`。
- `npm test`
  - 结果：通过，`2 passed`，`290 passed`。
- `npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：通过，当前 PC Node 仍监听 `*:7001`，未改 Clash 或系统代理。

## 剩余风险

- 本轮只调整 PC 端只读展示和回归测试，不执行真实 Nav2、不发送 manual/keyboard/delivery/stop 或 `/cmd_vel`。
- live 仍需要现场勾选行程前安全确认后，手动点击 ROS 重跑图上路线，才能验证同窗口 wheel raw L/R 是否非零。
