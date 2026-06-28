# PC Camera Shared Preview Common Aliases

sprint_type: micro

## 实际改动

- `RobotControlCameraMjpegStatusResponse` 新增通用只读别名：
  - `viewer_count`
  - `upstream_connected`
  - `has_recent_frame`
- `/api/robot-control/camera/mjpeg/status` 把上述字段分别镜像到：
  - `client_count/shared_preview_client_count`
  - `upstream_active/shared_preview_upstream_active`
  - `cached_frame_loaded/shared_preview_cached_frame_loaded`
- Robot Control summary 的 `readback_summary.camera` 同步新增同名字符串别名，让 summary 和独立 camera status 都能直接表达“几个页面共享、是否连接同一上游、是否已有最近帧”。
- 同步更新 App fixture、catalog camera status 测试、README 和产品文档。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "camera MJPEG status"`
  - `Test Files 1 passed (1)`
  - `Tests 6 passed | 154 skipped (160)`
- 已通过：`npm --prefix pc-tools/workstation run build`
  - TypeScript、Vite client build、server TypeScript 均通过。
  - Vite 仍有既有 chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 375 passed (375)`
- 已重启 PC workstation API 到 `0.0.0.0:7001`，监听进程为 `node`。
- 已通过：只读验证 `/api/robot-control/camera/mjpeg/status`。
  - `proxy_status=status_loaded`
  - `client_count=0`
  - `shared_preview_client_count=0`
  - `viewer_count=0`
  - `upstream_active=false`
  - `shared_preview_upstream_active=false`
  - `upstream_connected=false`
  - `cached_frame_loaded=false`
  - `shared_preview_cached_frame_loaded=false`
  - `has_recent_frame=false`
  - `shared_capture=true`
  - `exclusive_camera_claim=false`
  - `shared_preview_contract=single_shared_capture_for_multiple_clients`
  - `preview_status=source_first_frame_failed`
  - `robot_control_executed=false`
- 已通过：只读验证 `/api/robot-control/summary` 的 `readback_summary.camera`。
  - `viewer_count=0`
  - `shared_preview_client_count=0`
  - `upstream_connected=false`
  - `shared_preview_upstream_active=false`
  - `has_recent_frame=false`
  - `shared_preview_cached_frame_loaded=false`
  - `safe_to_control=false`
  - `safe_command_boundary.robot_control_executed=false`

## 剩余风险

- 本轮只补 PC Node 只读状态别名，不创建 MJPEG client、不重启相机、不打开第二条相机上游。
- live 当前上车相机仍报告 UVC 无首帧；这不是页面独占，仍需要检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。
- 未获得本轮现场安全确认前，不做真实运动、键盘连续手控、自由移动或自动驾驶执行验证。
