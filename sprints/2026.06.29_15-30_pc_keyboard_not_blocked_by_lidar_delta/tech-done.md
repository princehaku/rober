# PC 键盘手控不再被雷达移动记录误导

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 中修正普通首页的雷达移动记录提示：雷达 delta 是运动/建图材料证据，不再表述成键盘手控解锁前置。
- 将“之后键盘手控才会解锁”改为“只影响运动/建图材料，不阻塞键盘手控”，并覆盖雷达未运行、雷达运行但未取到 delta、已试动但 delta 未通过三类提示。
- 在 `pc-tools/workstation/test/App.test.ts` 更新首页断言，防止旧的“雷达解锁键盘”文案回流，同时保留键盘仍需安全确认、按住才动、不会自动发车的行为。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "renders Robot Control V1|allows confirmed low-speed motion|points the keyboard arm button|counts nonzero wheel readback from keyboard pulses"` 通过：5 tests passed。
- `npm --prefix pc-tools/workstation test` 通过：2 files passed, 368 tests passed。
- `npm --prefix pc-tools/workstation run build` 通过；仅保留 Vite chunk size 既有警告。
- 只读查询 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 显示当前 live 合同为 `keyboard_control_start_ready=true`、`keyboard_control_mode=bounded_repeating_manual_pulse`、`free_roam.status=start_ready`，雷达仍为 stopped/stale。

## 剩余风险

- 本轮没有现场安全确认，因此没有触发键盘手控、底盘试动、自由移动、雷达启动或 Nav2 执行。
- 键盘连续手控最终验收仍需现场勾选安全确认后按住 W/A/S/D 或方向键，读到连续低速脉冲、停止收口和 wheel L/R 证据。
- 雷达移动记录仍是建图/运动材料的一部分；本轮只把它从“键盘是否能动”的普通用户门禁里解耦。
