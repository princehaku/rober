# PC 键盘连续手控验收 DOM

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通首屏 `keyboard-control-panel` 和 `plain-keyboard-continuous-proof` 增加键盘连续手控验收 packet DOM 属性。
  - DOM 直接暴露 ready、motion verified、安全确认、hold-to-move、pulse interval/duration、stop triggers、manual/stop/feedback/summary endpoint 和 readback endpoint。
  - 明确只读复验边界：readback 不发 motion，不启动 Nav2/manual/keyboard/free-roam/map runtime，不提交 delivery，也不执行 stop。
- `pc-tools/workstation/test/App.test.ts`
  - 增加普通首屏默认状态断言，锁定键盘连续手控验收 packet 与只读复验边界。
- `docs/product/pc_tools_workstation.md`
  - 补充 PC 键盘连续手控验收 DOM 合同。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 233 passed (233)`
- 通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`
  - `Test Files 2 passed (2)`
  - `Tests 190 passed (190)`
- 通过：`npm --prefix pc-tools/workstation run lint`
- 通过：`npm --prefix pc-tools/workstation run build`
  - Vite 输出既有 chunk size warning；构建成功。
- 通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Test Files 3 passed (3)`
  - `Tests 423 passed (423)`
- 通过：重启 `0.0.0.0:7001`
  - 当前监听：`node` PID `69833`，`TCP *:7001 (LISTEN)`
  - `GET http://127.0.0.1:7001/` -> `200`
  - `GET http://127.0.0.1:7001/map` -> `200`
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 只读 smoke 读到：`keyboard_ready=true`、`keyboard_continuous_ready=true`、`keyboard_continuous_motion_verified=false`、固定 keyboard manual/stop/feedback/summary endpoint 和 `keyboard_acceptance_plain`。

## 剩余风险

- 本轮只补 PC DOM 可验收证据，不执行真实键盘手控、不发送运动命令；wheel raw L/R 非零和 stop settled 仍需现场安全确认后实车验证。
- 未触碰两份历史 dirty artifact：`sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`、`sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`。
