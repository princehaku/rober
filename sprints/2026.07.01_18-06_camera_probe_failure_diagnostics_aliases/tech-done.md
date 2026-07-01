# 相机首帧 probe 失败诊断 alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `POST /api/robot-control/camera/first-frame/probe` 在 `probe_failed` / HTTP 502 时也补齐画面 WYSIWYG 诊断 alias。
  - probe 失败体现在会直接返回 `camera_first_frame_ready`、`frame_observed`、`source_diagnosis_*`、`camera_usb_*`、`camera_hardware_action_*`、`camera_blocks_mapping_start`、`camera_blocks_free_move=false`、固定 status/summary 端点和 no-motion/no-runtime 标志。
  - 诊断来源为同一小车地址的只读 `/api/camera/health`，不创建新 MJPEG client，不打开额外相机流，不启动建图 runtime，不发送任何运动命令。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 `RobotControlCameraFirstFrameProbeProxyResponse` 合同，避免失败体关键字段继续是类型外字段或现场读到 `null`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补充上车 probe 502 + health 显示 USB 12M/full-speed/not-exclusive 的合同测试。
- `docs/product/pc_tools_workstation.md`
  - 同步 probe 失败体必须直接暴露相机诊断和 no-motion 边界的产品合同。

## 验证结果

- 已通过：`git diff --check`
- 已通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "camera first-frame probe can request backend smoke"`，1 file passed，1 passed / 180 skipped。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，9 tests passed。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "live-summary|camera first-frame probe"`，1 file passed，5 passed / 176 skipped。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "camera MJPEG status derives non-exclusive|camera first-frame probe can request backend smoke"`，1 file passed，2 passed / 179 skipped。
- 已通过：`cd pc-tools/workstation && npm test`，3 files passed，421 tests passed。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`，Vite/TS build 成功；仍有既有 bundle >500 kB 提示。
- 已通过：重启 PC Node 到 `0.0.0.0:7001`，实际监听 PID `65351`。
- 已通过：真实 no-motion `POST http://127.0.0.1:7001/api/robot-control/camera/first-frame/probe?baseUrl=http://192.168.1.11:8787` 返回 HTTP 502 / `probe_failed`，但失败体已直接带出 `camera_first_frame_ready=false`、`frame_observed=false`、`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`source_diagnosis_not_exclusive=true`、`camera_usb_speed=12M`、`camera_usb_full_speed_detected=true`、`camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`robot_control_executed=false`、`sends_motion_when_clicked=false`、`starts_map_runtime=false`、`dangerous_true_fields=[]` 和固定 status/summary 端点。

## 剩余风险

- 本轮只修 PC probe 失败体诊断完整性；真实相机仍受 USB 12M full-speed / 首帧失败影响，建图启动仍差 `camera_first_frame`。
- 本轮不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
