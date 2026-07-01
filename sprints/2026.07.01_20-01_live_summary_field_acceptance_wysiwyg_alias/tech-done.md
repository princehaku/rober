# Live summary field acceptance WYSIWYG alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlFieldAcceptanceWysiwygRefreshMode`，表达 `camera_only`、`radar_map_only`、`map_only`、`all_wysiwyg` 和 `none`。
  - `/api/robot-control/live-summary` 合同补齐现场验收包与 WYSIWYG 刷新字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - summary 顶层新增 `field_acceptance_wysiwyg_refresh_mode`，与 PC 现场验收按钮的聚焦刷新口径一致。
  - `field_acceptance_wysiwyg_refresh_sequence` 改为按 mode 聚焦；只缺相机时只暴露相机首帧 probe、MJPEG status 和 summary。
- `pc-tools/workstation/src/server/index.ts`
  - live-summary 顶层透出 `field_acceptance_packet`、WYSIWYG 缺口、刷新 endpoint/label/sequence/mode 和所有 no-motion guard 字段。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖 summary 顶层与 packet 内的 `field_acceptance_wysiwyg_refresh_mode`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 live-summary 顶层字段与 summary 保持一致，并保持不启动 Nav2/manual/keyboard/free-roam/radar lifecycle/map runtime/delivery/stop。
- `docs/product/pc_tools_workstation.md`
  - 记录 live-summary 现场验收扁平字段和刷新 mode 口径。

## 验证结果

- `npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts -t "field acceptance|live-summary"`：通过，1 passed / 189 skipped。
- `npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts`：通过，9 passed。
- `npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts`：通过，181 passed。
- `npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`：通过，190 passed。
- `npm --prefix pc-tools/workstation run lint`：通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 仅保留既有 chunk size warning。
- `npm --prefix pc-tools/workstation test -- --run`：通过，3 files / 422 passed。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID 90208。
- 只读 smoke：
  - `GET /`：200。
  - `GET /map`：200。
  - `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787`：`proxy_status=refresh_forwarded`、`robot_control_executed=false`、`last_result_status=refreshed`。
  - `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787`：`radar_overlay_status=loaded`、`radar_overlay_current_point_count=127`、`radar_overlay_needs_refresh=false`、`robot_control_executed=false`。
  - `GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787`：`field_acceptance_wysiwyg_missing_surface_ids=["camera"]`、`field_acceptance_wysiwyg_refresh_mode=camera_only`、`field_acceptance_wysiwyg_refresh_sequence=["/api/robot-control/camera/first-frame/probe","/api/robot-control/camera/mjpeg/status","/api/robot-control/summary"]`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=127`，所有 WYSIWYG refresh motion/control guard 均为 false。

## 剩余风险

- 本轮只补只读合同和现场脚本可见性，不触发真实 Nav2、键盘、自由移动、建图、delivery complete 或 stop。
- 当前真实缺口仍是相机首帧、同窗口 wheel L/R 非零、delivery success、键盘/自由移动真实运动验收；没有新的现场安全确认前不能发运动命令。
