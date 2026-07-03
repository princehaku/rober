# 相机 OpenCV 打不开设备状态修复

## sprint_type

micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`：把 `opencv_capture_not_opened` 纳入共享相机首帧失败集合，避免上车 `/api/camera/health` 在刚失败后仍误报成“未探测”。
- `pc-tools/workstation/src/server/index.ts`：PC MJPEG status 把 health `source_failure_reason=none` 与 `media_diagnostics.last_offer_error.failure_reason=opencv_capture_not_opened` 分开处理；last offer 已经证明首帧失败时，返回 `source_first_frame_failed`、`uvc_no_frame_not_exclusive` 和普通用户处理动作。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 同步消费 last offer 首帧失败，不再把 OpenCV open failure 保持为 `source_not_probed`。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：新增 OpenCV open failure 回归，锁定只读、不创建 MJPEG client、非独占无帧、`camera_hardware_action_required=true` 和 `camera_blocks_free_move=false`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步当前口径：ROS2/RViz2/Foxglove 只作工程观察，普通用户继续用 PC 大地图；相机仍无真实首帧时显示检查输入/供电动作，不阻塞地图、WASD、自由移动或 Nav2 控制入口。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "OpenCV open failure|first-frame total timeout"`，3 passed / 186 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，16 passed。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript/Vite 构建通过；仅保留既有 Vite 大 chunk 提示。
- 通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`。
- 通过：已复制脚本到 `root@192.168.1.11:/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`，并重启 `trashbot-local-webrtc-camera.service`；`systemctl is-active` 返回 `active`。
- 通过：本机 PC Node 已重启到 `*:7001`，`curl -I http://127.0.0.1:7001/map` 返回 `HTTP/1.1 200 OK`。
- 现场读回：请求 PC 共享 MJPEG 后仍返回 `502 {"error":"first_frame_total_timeout"}`，但 `GET /api/robot-control/camera/mjpeg/status` 已返回 `preview_status=source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、`source_usage_owner_count=0`、`camera_usb_speed=480M`、`exclusive_camera_claim=false`、`camera_hardware_action_required=true`、`camera_hardware_action_label=检查摄像头输入/供电后复测`、`camera_blocks_free_move=false`。
- 现场 summary 读回：`map_display_default_zoom_percent=800%`、`map_preview_status=loaded`、`path_preview_point_count=18`、`route_target_visible=true`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=75`、`keyboard_continuous_motion_verified=true`、`free_move_without_camera_allowed=true`、`readback_summary.camera.status=source_first_frame_failed`。

## 剩余风险

- 本轮修复状态归因和用户可理解动作，不代表 DV20 已经输出真实视频帧；现场仍需检查摄像头输入、线/接口/供电，或换 known-good UVC 后复测。
- 本轮未重新执行真实 Nav2 行程、delivery success 或 wheel raw L/R 非零闭环；地图、WASD 和已有路线读回保持当前现场证据。
