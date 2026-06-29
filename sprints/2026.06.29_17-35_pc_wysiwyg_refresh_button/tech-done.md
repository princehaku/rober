# PC 当前所见只读刷新入口

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前所见` 标题行新增 `刷新当前所见（只读）` 按钮。
  - 按钮复用 `refreshPlainConsole()`，一次刷新 Robot Control summary、地图预览、雷达状态和共享 MJPEG 状态。
  - pending 时显示 `刷新总览中`、`刷新地图画面中` 或 `刷新画面状态中`，避免误以为在启动雷达或发车。
- `pc-tools/workstation/test/App.test.ts`
  - 补普通首屏回归断言：点击 `刷新当前所见（只读）` 会调用 summary、map preview、radar status、camera mjpeg status。
  - 同时断言不会调用 radar start、Nav2 goal execute、base manual 或 free-roam start。
- `docs/product/pc_tools_workstation.md`
  - 同步记录当前所见只读刷新入口和安全边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 216 skipped (217)`。
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`，`Tests 382 passed (382)`。
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成；Vite 仍提示既有 bundle 大小 warning。
- 通过：`git diff --check`
- 通过：7001 本地服务重启。
  - `node` 监听 `TCP *:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读 live `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - `primary_ready_action_item_id=free_move`
  - `ready_action_ids=free_move,keyboard_continuous_control,nav2_route_execution`
  - `camera_status=source_first_frame_failed`
  - `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `radar_status=radar_stopped`
  - `radar_lifecycle_running=false`
  - `radar_overlay_point_count=0`
  - `nav2_goal_ready=true`
  - `nav2_lifecycle_state=stopped`
  - `nav2_route_execution_status=goal_succeeded_wheel_feedback_not_proven`
  - `keyboard_status=start_ready`
  - `free_roam_status=start_ready`
  - `free_move_start_ready=true`

## 剩余风险

- 本轮只新增 PC 首屏只读刷新入口，没有现场安全确认，因此没有启动自由移动、键盘连续手控、Nav2、雷达、建图或底盘运动。
- live 当前仍是：相机 UVC 无首帧、雷达 lifecycle stopped、Nav2 路线可重跑但同窗口轮速 L/R 未非零；真实完成仍需现场安全确认后的运动验证。
