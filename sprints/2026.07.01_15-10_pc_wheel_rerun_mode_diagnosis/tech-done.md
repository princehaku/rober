# PC 轮速复验模式诊断前置

sprint_type: micro

## 实际改动

- `live_closure_summary` 新增轮速复验 A/B 控制模式诊断字段，直接暴露上次底盘模式、下次复验模式、非零命令次数、最新非零命令模式和控制链诊断文案。
- 普通首屏当前卡点与轮速复验计划显示该诊断，现场能看到“上次 PWM/ROS 已有非零命令但轮速仍为 0/0，下次切换模式复验”，并明确这不是雷达、相机或地图所见缺口。
- 更新测试和产品文档，保持所有按钮仍为聚焦或只读读回，不触发运动命令。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "minimal precheck fields for same-window wheel rerun"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "keeps live closure wheel rerun as a focus-only Nav2 action"`：通过，1 passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单包 chunk 超过 500 kB，这是既有体积提醒，不影响本轮功能。
- `cd pc-tools/workstation && npm test`：通过，3 files / 418 tests。
- `git diff --check`：通过。
- 运行态只读确认：PC API 已重启到 `0.0.0.0:7001`，`GET /api/robot-control/live-summary` 返回 `status=needs_wheel_rerun`、`wheel_rerun_mode_rerun_status=pending_ros_rerun_after_pwm`、`wheel_rerun_base_command_nonzero_count=49`，诊断文案包含“不是雷达、相机或地图所见缺口”，地图默认缩放仍为 `600%`。

## 剩余风险

- 本轮只前置诊断和下一次复验模式，不自动发送 Nav2/manual/free-roam/stop；真实轮速非零仍需要现场勾安全确认后执行复验。
