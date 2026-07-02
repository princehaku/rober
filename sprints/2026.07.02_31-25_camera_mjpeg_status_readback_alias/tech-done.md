# Camera MJPEG Status Readback Alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 `RobotControlCameraMjpegStatusResponse` 增加 `camera_mjpeg_status_readback_only: true`。
- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/camera/mjpeg/status` 回包直接返回 `camera_mjpeg_status_readback_only=true`，与既有 `readback_only`、`camera_status_readback_only` 同源。
- `pc-tools/workstation/test/catalog.test.ts`：补充 camera MJPEG status 直连只读 alias 断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录该接口按接口名暴露只读状态，不独占相机、不启动建图或运动链路。

## 验证结果

- 通过：`npm test -- test/catalog.test.ts`，`Test Files 1 passed (1)`，`Tests 183 passed (183)`。
- 通过：`npm run build`，TypeScript app/server 与 Vite build 均完成；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001` 后 live 读取 `/api/health`，确认 `workstation_listen_address=http://0.0.0.0:7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：live 读取 `/api/robot-control/camera/mjpeg/status`，确认 `readback_only=true`、`camera_status_readback_only=true`、`camera_mjpeg_status_readback_only=true`、`shared_preview_readback_only=true`、`starts_camera_exclusive_capture=false`、`starts_nav2=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`stops_motion=false`。

## 剩余风险

- 本轮只补相机共享预览状态接口的只读 alias，不解决 USB 12M / `first_frame_total_timeout` 硬件首帧 blocker。
- 运动 HIL 证据仍需要现场安全确认后执行 Nav2、键盘连续控制和自由移动读回。
