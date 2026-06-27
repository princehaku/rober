# PC 键盘当前事实 pulse 合同

sprint_type: micro

## 实际改动

- 更新 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `当前事实` 的键盘行现在从 `safe_command_boundary.keyboard_jog_duration_ms` 和 `keyboard_jog_interval_ms` 读取 bounded pulse 参数，显示按住连续低速脉冲、松开/失焦/切页停止的真实合同。
- 更新 `pc-tools/workstation/test/App.test.ts`：默认 Robot Control 首屏测试锁定“240ms/每 260ms”的键盘连续手控文案，防止退回只写“可启用”的模糊提示。
- 更新 `docs/product/pc_tools_workstation.md`：同步记录该行只是只读事实翻译，不自动启用键盘、不发送 manual pulse 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- App.test.ts --testNamePattern "renders Robot Control V1|keyboard control"`；结果 `1 passed`，`6 passed | 157 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅有既有 Vite chunk size warning。
- 通过：`npm test`；结果 `2 passed`，`284 passed`。
- 通过：`git diff --check`。
- 通过：PC Node 已用 `launchctl submit -l rober.pc.api.7001` 重新绑定 `0.0.0.0:7001`，`launchctl print` 显示 `state=running`，`lsof` 显示 `TCP *:7001 (LISTEN)`，`curl -I http://127.0.0.1:7001/` 返回 `HTTP/1.1 200 OK`；只读 `/api/robot-control/summary` 返回：
  - `keyboard_control_mode=bounded_repeating_manual_pulse`
  - `keyboard_reuses_manual_gate=true`
  - `keyboard_control_start_ready=true`
  - `keyboard_jog_interval_ms=260`
  - `keyboard_jog_duration_ms=240`
  - `keyboard_stop_triggers=key_released/window_blur/page_hidden/direction_changed/button_stop`

## 剩余风险

- 本轮只修普通首屏 WYSIWYG 文案和测试，不触发真实键盘手控、不验证真实底盘运动。
- 相机首帧、Nav2 同窗口 wheel raw L/R 非零、delivery success 仍需后续现场或 mock/硬件验证继续收口。
