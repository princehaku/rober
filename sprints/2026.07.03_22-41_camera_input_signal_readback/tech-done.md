# 相机输入信号读回收窄

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/camera/mjpeg/status` 新增 `camera_input_signal_check_required`、`camera_input_signal_check_label`、`camera_input_signal_check_plain`，在非独占、480M、高速 USB、无 UVC transport error 但仍无首帧时指向输入信号/线/接口/供电排查。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 的 `readback_summary.camera` 同步输出同一输入信号处理合同，避免现场只读 summary 时还要推断。
- `pc-tools/workstation/src/shared/contracts.ts`：补充可选类型字段，兼容旧 fixture。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：锁定 OpenCV/open failure 与 no-frame 诊断下的新字段。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：记录当前相机无帧已经从 PC 页面/独占/低速 USB 收窄到输入信号、视频线、接口、供电或 known-good UVC 复测。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "OpenCV open failure|first-frame total timeout"`，3 passed / 186 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "OpenCV camera open failure|camera summary"`，2 passed / 14 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，16 passed。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript/Vite 构建通过；仅保留既有 Vite 大 chunk 提示。
- 现场硬件对照：停止 `trashbot-local-webrtc-camera.service` 后确认 `/dev/video1` 无 owner，`v4l2-ctl` 直抓 `MJPG@640x480` 与 `YUYV@320x240` 都 `select timeout` 且输出 0 字节；`ffmpeg` 直抓 MJPG/YUYV 10 秒没有任何帧。
- 现场服务验证：PC Node 已重启到 `*:7001`，`curl -I http://127.0.0.1:7001/map` 返回 200。触发 `/api/robot-control/camera/mjpeg` 后仍返回 `first_frame_total_timeout`，但 `/api/robot-control/camera/mjpeg/status` 已返回 `camera_input_signal_check_required=true`、`camera_input_signal_check_label=检查摄像头输入信号/供电后复测`、`camera_usb_speed=480M`、`source_usage_owner_count=0`、`exclusive_camera_claim=false`、`camera_blocks_free_move=false`。
- 现场 summary 验证：`map_preview_status=loaded`、`path_preview_point_count=18`、`route_target_visible=true`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=93`、`keyboard_continuous_motion_verified=true`、`free_move_without_camera_allowed=true`、`readback_summary.camera.camera_input_signal_check_required=true`。

## 剩余风险

- 真实图传仍没有视频帧，本轮证明软件链路已走到 V4L2/ffmpeg 直接抓取仍 0 字节；需要现场检查摄像头/采集卡输入信号、视频线、接口、供电，或换 known-good UVC 后复测。
- 本轮没有重新跑真实 Nav2 路线、delivery success 或 wheel raw L/R 非零闭环；仅保持地图、WASD 和自由移动入口不被相机缺口阻塞。
