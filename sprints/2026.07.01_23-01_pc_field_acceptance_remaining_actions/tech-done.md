# PC 现场验收剩余动作分组

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 和 `field_acceptance_packet` 新增三类剩余动作字段：
  - `safety_confirm_ready_step_ids`：只差现场安全确认的运动验收。
  - `hardware_action_ids`：需要先处理的设备动作，例如相机 USB/full-speed 恢复。
  - `no_motion_readback_action_ids`：可随时执行的只读复验动作。
- 普通首屏 `plain-field-acceptance-packet` 新增同名 DOM data 字段和 `plain-field-acceptance-remaining-actions` 可见短句。
- 可见短句保持普通用户口径：使用“设备处理、复验全部读数、刷新当前所见、刷新雷达贴图”，不把 Nav2/manual/free-roam/lifecycle 等工程词放回首屏。
- `pc-tools/README.md` 同步记录该只读合同和不发车边界。

## 验证结果

- 已通过：`npm test -- robotControlSummary.test.ts App.test.ts`
  - 结果：`Test Files 2 passed (2)`，`Tests 245 passed (245)`。
- 已通过：`npm run build`
  - 结果：TypeScript app/server 和 Vite production build 通过；仅保留既有 chunk size warning。
- 已通过：`git diff --check`
  - 结果：无 whitespace error。
- 已通过：重启 Node 工作站并读取真实 `GET /api/robot-control/summary`
  - 监听：`0.0.0.0:7001`，PID `43150`。
  - 小车地址：`http://192.168.1.11:8787`。
  - 结果：`status=needs_wheel_rerun`，`live_wysiwyg_missing_surface_ids=["camera"]`，`radar_overlay_status=loaded`。
  - 结果：`field_acceptance_safety_confirm_ready_step_ids=["run_nav2_route","hold_keyboard","start_free_move"]`。
  - 结果：`field_acceptance_hardware_action_ids=["camera_usb_recovery"]`。
  - 结果：`field_acceptance_no_motion_readback_action_ids=["readback_all","refresh_current_wysiwyg"]`。
  - 结果：验收包 `sends_motion_when_clicked=false`，`starts_nav2/manual/free_roam/map_runtime=false`。

## 剩余风险

- 当前改动不发送运动命令，也不替现场安全确认；Nav2 路线执行、键盘连续手控、自由移动仍需要用户在现场勾选安全确认后手动触发。
- 相机若仍为 USB 12M/full-speed 或无首帧，建图首帧仍会被阻塞；低速自由移动不被该相机缺口阻塞。
