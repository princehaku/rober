# PC 键盘连续控制 readback 别名补齐

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 抽出 `RobotControlKeyboardReadbackSummary`，让 keyboard 读回结构可复用。
  - `readback_summary` 增加 `keyboard_control` 和 `keyboard_teleop`，均与 `keyboard` 同构。
  - 顶层增加 `keyboard_control_summary` 和 `keyboard_teleop_summary`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 正常 summary 和 blocked/not-loaded fallback 都复用同一个 keyboard readback 对象。
  - `readback_summary.keyboard`、`readback_summary.keyboard_control`、`readback_summary.keyboard_teleop` 保持完全一致。
  - 顶层 `keyboard_summary`、`keyboard_control_summary`、`keyboard_teleop_summary` 也保持完全一致。
- `pc-tools/workstation/test/catalog.test.ts`
  - 扩展正常和 blocked 两条 summary 路径的 alias 等值断言。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 keyboard/control/teleop 三种命名都可读同一份连续手控事实。

## 验证结果

- `npm run build`：通过。
- `git diff --check`：通过。
- `npm test -- catalog.test.ts`：通过，`167 passed`。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID 为 `15116`。
- live `GET http://127.0.0.1:7001/api/robot-control/summary`：
  - `readback_summary.keyboard == readback_summary.keyboard_control` 为 `true`
  - `readback_summary.keyboard == readback_summary.keyboard_teleop` 为 `true`
  - `keyboard_summary == keyboard_control_summary` 为 `true`
  - `keyboard_summary == keyboard_teleop_summary` 为 `true`
  - `readback_summary.keyboard.start_ready=true`
  - `readback_summary.keyboard_control.start_ready=true`
  - `readback_summary.keyboard_teleop.start_ready=true`
  - `readback_summary.keyboard.next_action_plain` 包含“按住 W/A/S/D”
  - `safe_command_boundary.keyboard_control_start_ready=true`
  - `safe_command_boundary.keyboard_teleop_start_ready=true`

## 剩余风险

- 本轮只补 PC summary/readback 字段别名，不启用键盘、不发送 manual pulse、不调用 stop 或 `/cmd_vel`。
- 真正连续键盘手控仍需现场勾选安全确认后按住方向键/WASD 进行实车验证。
