# sprint_type: micro

## 实际改动

- PC 普通键盘手控 `keyboard-live-status` 在“未启用”和“等待按键”两种静止状态下，直接显示连续手控节奏：
  - `按住后约每 0.26 秒发送 0.24 秒低速脉冲，松开/失焦/切页会停。`
- 这样普通用户不用展开或读长 guide，也能在状态行看到“键盘连续控制”的真实机制和停止边界。
- 本轮只改前端状态文案和测试；没有触发键盘脉冲、底盘 manual、Nav2、自由移动、雷达启动或 cmd_vel。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "keyboard"`：通过，21 passed。
- `npm --prefix pc-tools/workstation test`：通过，367 passed。
- `npm --prefix pc-tools/workstation run build`：通过，Vite 仍提示现有 chunk 大于 500 kB 的非阻塞 warning。
- 只读 live `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`：通过，返回 `keyboard_control_mode=bounded_repeating_manual_pulse`、`keyboard_reuses_manual_gate=true`、`keyboard_jog_duration_ms=240`、`keyboard_jog_interval_ms=260`、`manual_motion_entry_status=controlled_jog_requires_safety_confirmation_only`，且 next action 明确“勾选现场安全确认后点击启用键盘；按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页会停”。

## 剩余风险

- 本轮没有现场安全确认，因此没有真实按住键盘，也没有产生 wheel raw L/R 非零或停止收口证据。
- PC 键盘连续控制的 UI 合同更清楚了，但完整验收仍需要现场按住方向键连续发出至少 2 次低速脉冲、松开自动停止，并读到同窗口 wheel raw L/R 非零。
