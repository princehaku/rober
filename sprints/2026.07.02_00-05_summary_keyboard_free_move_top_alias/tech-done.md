# Summary 顶层键盘连续控制与自由移动 Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增 PC 键盘连续控制 alias，全部与 `live_closure_summary` 同源：
  - `keyboard_continuous_minimal_precheck_safety_only`
  - `keyboard_continuous_safety_confirm_required`
  - `keyboard_continuous_enable_sends_motion=false`
  - `keyboard_continuous_hold_to_move_required=true`
  - `keyboard_continuous_pulse_interval_ms`
  - `keyboard_continuous_pulse_duration_ms`
  - `keyboard_continuous_stop_triggers`
  - `keyboard_continuous_wheel_feedback_acceptance`
  - `keyboard_safety_confirm_required`
  - `keyboard_hold_to_move_required`
  - `keyboard_pulse_interval_ms`
  - `keyboard_pulse_duration_ms`
  - `keyboard_stop_triggers`
  - `keyboard_acceptance_plain`
  - `keyboard_summary_endpoint`
- `GET /api/robot-control/summary` 顶层新增自由移动操作合同 alias：
  - `free_move_minimal_precheck_safety_only=true`
  - `free_move_safety_confirm_required`
  - `free_move_camera_preflight_required=false`
  - `free_move_radar_preflight_required=false`
  - `free_move_blocked_by_camera_wysiwyg=false`
  - `free_move_blocked_by_radar_wysiwyg=false`
  - `fixed_free_roam_start_endpoint=/api/robot-control/free-roam/autonomy/start`
  - `fixed_free_roam_stop_endpoint=/api/robot-control/free-roam/autonomy/stop`
- 同步更新 `RobotControlSummaryResponse` contract、`robotControlSummary.test.ts`、`catalog.test.ts` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts -t "map"`：通过，1 个 test file，5 passed，4 skipped。
- `npm test -- --run test/catalog.test.ts -t "live-summary"`：通过，1 个 test file，1 passed，180 skipped。
- `npm test`：通过，3 个 test files，421 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，当前监听 PID `6879`。
- 真实只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 顶层读回：
  - `keyboard_ready=true`
  - `keyboard_continuous_ready=true`
  - `keyboard_safety_confirm_required=true`
  - `keyboard_enable_sends_motion=false`
  - `keyboard_hold_to_move_required=true`
  - `keyboard_pulse_interval_ms=260`
  - `keyboard_pulse_duration_ms=240`
  - `keyboard_stop_triggers=[key_release,window_blur,page_hidden,direction_change,stop_button]`
  - `keyboard_continuous_wheel_feedback_acceptance=same_hold_window_wheel_lr_nonzero`
  - `free_move_start_ready=true`
  - `free_move_minimal_precheck_safety_only=true`
  - `free_move_safety_confirm_required=true`
  - `free_move_camera_preflight_required=false`
  - `free_move_radar_preflight_required=false`
  - `free_move_without_camera_allowed=true`
  - `free_roam_motion_without_radar_allowed=true`
  - `free_move_blocked_by_camera_wysiwyg=false`
  - `free_move_blocked_by_radar_wysiwyg=false`
  - `fixed_free_roam_start_endpoint=/api/robot-control/free-roam/autonomy/start`
  - `fixed_free_roam_stop_endpoint=/api/robot-control/free-roam/autonomy/stop`

## 剩余风险

- 本轮只修 summary 顶层读数，不启用键盘，不启动自由移动。
- 键盘连续控制和自由移动仍是会发运动命令的入口，真实执行必须先由现场 operator 勾安全确认。
- 本轮不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop，也不发布 `/cmd_vel`。
