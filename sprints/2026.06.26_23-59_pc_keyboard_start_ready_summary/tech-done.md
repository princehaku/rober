# PC 键盘手控 Start Ready Summary

sprint_type: micro

## 实际改动

- 在 `Robot Control summary` 的 `safe_command_boundary` 中新增 `keyboard_control_start_ready=true` 与 `keyboard_control_label=键盘手控（勾确认后可启用）`。
- 保持 `keyboard_control_enabled=false` 不变，继续表示 summary 本身不武装键盘、不发送 manual/stop；真实发车仍需要本地安全确认和用户显式按住方向键/WASD。
- 同步更新 PC 工作站产品文档，说明 start ready 与 enabled=false 的语义差异。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts`，`106 passed`。
- 通过：`cd pc-tools/workstation && npm test -- App.test.ts`，`140 passed`。
- 通过：`cd pc-tools/workstation && npm run build`，client/server TypeScript 与 Vite build 均通过；仅保留 Vite chunk size 提示。
- 通过：`git diff --check`。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` live smoke，返回 `keyboard_control_start_ready=true`、`keyboard_control_label=键盘手控（勾确认后可启用）`、`keyboard_control_enabled=false`、`keyboard_control_mode=bounded_repeating_manual_pulse`、`manual_motion_entry_status=controlled_jog_requires_safety_confirmation_only`。
- live 现场读数：PC Node 监听 `0.0.0.0:7001`；summary 为 `loaded_fail_closed_summary`、Robot API `readable`、`safe_to_control=false`；摄像头仍为 `source_first_frame_failed/first_frame_failed` 且 `source_usage_status=not_in_use`；底盘为 `fresh_base_status_readback`。

## 剩余风险

- 本轮只修 PC summary 语义，不改变键盘 pulse 发送链路，也不宣称 wheel raw L/R 已非零。
- 真车连续手控仍需现场按住方向键/WASD 后观察底盘 T1001 L/R 和外部视频确认。
