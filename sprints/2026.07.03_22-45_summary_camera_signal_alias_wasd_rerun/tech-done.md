# Summary 相机输入信号顶层读回与 WASD 复验

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：把 `camera_input_signal_check_required`、`camera_input_signal_check_label`、`camera_input_signal_check_plain` 从 `readback_summary.camera` 抬到 `live_closure_summary` 和 summary 顶层，现场 `jq` 不用钻 nested camera。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐 summary/live closure 类型合同。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：锁定 OpenCV/no-frame 场景下 readback、live closure、summary 顶层三处字段一致。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步当前口径和现场 WASD 前后退复验结果。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "OpenCV camera open failure"`，1 passed / 15 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，16 passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "OpenCV open failure|first-frame total timeout"`，3 passed / 186 skipped。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript/Vite 构建通过；仅保留既有 Vite 大 chunk 提示。
- 现场 PC Node 已重启到 `*:7001`，`curl -I http://127.0.0.1:7001/map` 返回 200。
- 现场 summary 顶层读回：`camera_input_signal_check_required=true`、`camera_input_signal_check_label=检查摄像头输入信号/供电后复测`、`map_preview_status=loaded`、`path_preview_point_count=18`、`route_target_visible=true`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=93`、`free_move_without_camera_allowed=true`。
- 现场 WASD/手控复验：PC `/api/robot-control/base/manual` 前进和后退短脉冲均返回 `proxy_status=command_forwarded`、`base_command_mode=ros`、`feedback_mode=realtime`、`command_result_ok=true`、`stop_result_ok=true`、`motion_signal_observed=true`、`imu_attitude_delta_observed=true`；随后 stop 返回 `command_forwarded/stopped`。

## 剩余风险

- 前进/后退同窗口 `wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_latest_raw_left/right=0/0`，所以只能证明 PC/API/ROS/bridge/运动信号链路，不证明 wheel raw L/R 非零。
- 真实图传仍没有视频帧；当前已收窄到摄像头输入信号、视频线、接口、供电或 known-good UVC 复测。
