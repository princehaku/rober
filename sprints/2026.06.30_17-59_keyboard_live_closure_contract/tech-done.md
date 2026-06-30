# Keyboard Live Closure Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlLiveClosureSummary` 新增键盘连续手控合同字段：安全-only 最小预检、启用不发车、按住才发脉冲、pulse 间隔/时长、停止触发、同窗口 wheel L/R 验收和固定 manual/stop endpoint。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `buildLiveClosureSummary()` 输出上述字段，让外部脚本只读 `GET /api/robot-control/summary` 也能判断键盘连续手控边界。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `plain-live-closure-summary` DOM 同步暴露键盘连续手控字段，便于现场脚本验收。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 补充 summary API 和 DOM 断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录键盘连续手控 live closure 合同。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，1 个测试文件、3 个测试通过。
- `npm test -- App.test.ts`：通过，1 个测试文件、225 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、402 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-CHcVVcAW.js` 与 `dist/assets/index-BCQK7HRw.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `87620`，新监听进程为 `node` PID `6233`，地址 `TCP *:7001`。
- live 只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `keyboard_continuous_control_ready=true`、`keyboard_continuous_minimal_precheck_safety_only=true`、`keyboard_continuous_safety_confirm_required=true`、`keyboard_continuous_enable_sends_motion=false`、`keyboard_continuous_hold_to_move_required=true`、`keyboard_continuous_pulse_interval_ms=260`、`keyboard_continuous_pulse_duration_ms=240`、`keyboard_continuous_stop_triggers=key_release,window_blur,page_hidden,direction_change,stop_button`、`keyboard_continuous_wheel_feedback_acceptance=same_hold_window_wheel_lr_nonzero`、`fixed_keyboard_manual_endpoint=/api/robot-control/base/manual`、`fixed_keyboard_stop_endpoint=/api/robot-control/base/stop`。本 smoke 未发送任何运动请求。

## 剩余风险

- 本轮只补只读 API/DOM 合同，不启用键盘、不发送 manual pulse、不发送 stop、不执行 Nav2 或 `/cmd_vel`。
- 真实键盘连续手控仍需要现场安全确认后，在同一次按住窗口验证 wheel L/R 非零和松开 stop 收口。
