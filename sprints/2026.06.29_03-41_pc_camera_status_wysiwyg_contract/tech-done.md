# PC Camera Status WYSIWYG Contract

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `RobotControlCameraMjpegStatusResponse` 增加 `preview_visible_status`、`preview_visible_plain`、`camera_wysiwyg_status_plain` 和 `camera_wysiwyg_next_action_plain`。
- `pc-tools/workstation/src/server/index.ts`：让 `/api/robot-control/camera/mjpeg/status` 直接返回共享画面是否可见的 WYSIWYG 白话，区分缓存帧可见、等待首帧、源头首帧失败、blocked 和 idle。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补充默认 fixture、缓存帧可见、idle 未可见、UVC 无首帧未可见的断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录独立 camera status endpoint 的只读合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "camera MJPEG status"`：通过，1 个文件，6 个测试通过，152 个跳过。
- `npm --prefix pc-tools/workstation test`：通过，2 个文件，373 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 保留既有 chunk size warning。
- 7001 本地 live 只读复验：`GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status` 返回 `proxy_status=status_loaded`、`preview_status=source_first_frame_failed`、`preview_visible_status=not_visible_source_first_frame_failed`、`camera_wysiwyg_status_plain=画面未可见：不是页面独占：USB Composite Device: DV20 USB  (usb-5310000.usb-1) 当前没人占用，但 UVC 设备没有输出视频帧；检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。`、`camera_wysiwyg_next_action_plain=检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。`、`shared_capture=true`、`shared_preview_exclusive_camera_claim=false`、`source_diagnosis_not_exclusive=true`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补 `/api/robot-control/camera/mjpeg/status` 的只读响应合同，不创建 MJPEG client、不打开额外 camera stream、不重启相机、不发送 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- live 相机仍显示 UVC 源头无首帧；需要现场检查 USB、摄像头输入/供电或换 known-good UVC 复测。
