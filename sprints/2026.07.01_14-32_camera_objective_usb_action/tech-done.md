# 相机 WYSIWYG 顶层目标动作收口

sprint_type: micro

## 实际改动

- 执行 no-motion 相机复测链路：首帧 probe、MJPEG status、live-summary，并通过 SSH 只读确认 USB/video 拓扑。
- `objective_audit_summary_plain` 在相机硬件动作已确认时，把相机缺口从 `画面未显示` 升级为 `画面未显示（换高速USB后复测）`。
- 产品文档同步该合同：只有 `camera_hardware_action_required=true` 时才把硬件动作带入顶层四项目标摘要；该字段只读，不启动 camera offer、建图 runtime 或任何运动命令。

## 验证结果

- 只读硬件事实：`lsusb -t` 显示 DV20 UVC 摄像头挂在 `12M` OHCI full-speed USB 总线上；`v4l2-ctl --list-devices` 显示 DV20 为 `/dev/video1`/`/dev/video2`；`fuser -v /dev/video0 /dev/video1 /dev/video2` 无 holder 输出。
- `POST /api/robot-control/camera/first-frame/probe` 返回 `remote_http_status=503`、`status=first_frame_timeout`、`failure_reason=deadline_expired`、`robot_control_executed=false`、`hard_dangerous_true_fields=[]`。
- `GET /api/robot-control/camera/mjpeg/status` 返回 `status=source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_failure_reason=first_frame_total_timeout`、`selected_path=/dev/video1`、`client_count=0`。
- `GET /api/robot-control/live-summary` 返回 `camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_usb_full_speed_detected=true`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`live_wysiwyg_missing_surface_ids=["camera"]`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "full-speed USB|mapping sensor|live closure"`，1 file passed，2 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "full-speed USB|objective|camera recovery"`，1 file passed，2 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 构建成功；保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，420 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读 `GET /api/robot-control/live-summary`，返回 `objective_audit_summary_plain=四项目标完成 1/4；下一项：行程/键盘/自由移动；未完成：行程/键盘/自由移动、画面未显示（换高速USB后复测）、建图启动还差画面首帧。`，并保持 `radar_map_points_visible=true`、`radar_overlay_status=loaded`、`map_current_visible=true`、`path_current_visible=true`、`free_move_start_ready=true`、`keyboard_ready=true`。

## 剩余风险

- 相机首帧仍未恢复；当前证据证明这不是页面独占，而是 DV20 挂在 USB 12M full-speed 后首帧不可读。
- 轮速 L/R 非零、完整 Nav2 路线现场执行、delivery success 和键盘连续手控仍需要显式安全确认后的运动验收；本轮未发任何运动命令。
