# PC 键盘连续控制 readback 别名

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlKeyboardReadbackSummary` 新增 `keyboard_continuous_control_ready`、`keyboard_hold_to_move_required`、`keyboard_enabled`、`keyboard_motion_verified`、`keyboard_continuous_pulse_verified`、`keyboard_current_hold_pulse_count`、`keyboard_best_continuous_pulse_count`、`keyboard_verified_min_forwarded_pulses`、`keyboard_safety_confirm_required`、`minimal_precheck_safety_only`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：把已有键盘连续控制合同抬成上述只读别名，方便现场脚本直接判断“可启用、按住才动、只需安全确认、当前未运动/未验收”。
- `pc-tools/workstation/test/catalog.test.ts`：补充键盘 readback 别名断言，防止后续又退回空字段。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts --run`，6 tests OK。
- 通过：`npm test -- test/catalog.test.ts --run`，177 tests OK。
- 通过：`npm test -- --run`，3 个测试文件、412 tests OK。
- 通过：`npm run build`，生成 `dist/assets/index-BoR-EUKp.js` 与 `dist/assets/index-BMxcT92A.css`；保留既有 Vite chunk size warning。
- 通过：PC Node 重启到 `0.0.0.0:7001` 后，live 只读 summary 返回 `keyboard_control_start_ready=true`、`keyboard_continuous_control_ready=true`、`keyboard_hold_to_move_required=true`、`keyboard_enabled=false`、`keyboard_motion_verified=false`、`keyboard_continuous_pulse_verified=false`、`keyboard_verified_min_forwarded_pulses=2`、`keyboard_safety_confirm_required=true`、`minimal_precheck_safety_only=true`、`safe_to_control=false`。

## 剩余风险

- 本轮只改 PC 只读 summary 字段，不启用键盘、不发送 manual pulse、stop、Nav2、free-roam、delivery 或 `/cmd_vel`。
- 键盘真实运动验收仍需现场勾选安全确认后按住方向键，在同一次按住窗口读到 wheel L/R 非零。
