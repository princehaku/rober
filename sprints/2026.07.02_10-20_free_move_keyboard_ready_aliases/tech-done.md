# Free Move Keyboard Ready Aliases

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增：
  - `current_keyboard_action_ready_for_safety_confirm`
  - `current_free_move_action_ready_for_safety_confirm`
  - `current_free_move_action_acceptance_plain`
  - `free_move_acceptance_plain`
- 自由移动验收文案固定说明：`启动后读取 free-roam latest、地图预览和 summary；相机、雷达不作为自由移动发车前置。`
- 同步 TypeScript contract、`robotControlSummary.test.ts` 和 `docs/product/pc_tools_workstation.md`。
- 这些字段只读，不自动勾安全确认，不发送 manual/free-roam/Nav2/建图/delivery/stop 或 `/cmd_vel`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts`：1 个测试文件、10 个用例通过。
- `npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`：3 个测试文件、429 个用例通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `92378`。
- live smoke `GET http://127.0.0.1:7001/api/robot-control/summary` 读回：
  - `current_keyboard_action_ready_for_safety_confirm=true`
  - `current_keyboard_action_missing_evidence=["same_hold_window_wheel_lr_nonzero","stop_after_release"]`
  - `current_free_move_action_ready_for_safety_confirm=true`
  - `current_free_move_action_acceptance_plain=启动后读取 free-roam latest、地图预览和 summary；相机、雷达不作为自由移动发车前置。`
  - `free_move_acceptance_plain=启动后读取 free-roam latest、地图预览和 summary；相机、雷达不作为自由移动发车前置。`
  - `free_move_ready=true`
  - `free_move_minimal_precheck_safety_only=true`
  - `free_move_camera_preflight_required=false`
  - `free_move_radar_preflight_required=false`
  - `free_move_blocked_by_camera_wysiwyg=false`
  - `free_move_blocked_by_radar_wysiwyg=false`
  - `mapping_start_missing_reasons=["camera_first_frame"]`

## 剩余风险

- 本轮没有执行任何 motion/control POST；完整 Nav2 行程、PC 键盘连续手控和自由移动真实运动仍需现场安全确认后验收。
- 相机首帧仍未恢复，建图启动仍缺 `camera_first_frame`；但低速自由移动不被该缺口阻塞。
