# 相机 USB 速度 summary 顶层 alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `GET /api/robot-control/summary` 顶层新增 `camera_usb_speed` 和 `camera_source_diagnosis_plain_hint`。
  - 字段直接来自 `live_closure_summary` / camera health 同源读回，让现场一条 `curl | jq` 就能看到 `12M`、USB full-speed 和“不是页面独占”的诊断。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 `RobotControlSummaryResponse` 顶层字段类型。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖 USB 12M 真实缺口场景的顶层 alias。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 summary 顶层字段与 `live_closure_summary` 同源。
- `docs/product/pc_tools_workstation.md`
  - 同步 summary 顶层相机 WYSIWYG 恢复 alias 合同。

## 验证结果

- 已通过：`git diff --check`
- 已通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，9 tests passed。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "live-summary"`，1 file passed，1 passed / 180 skipped。
- 已通过：`cd pc-tools/workstation && npm test`，3 files passed，421 tests passed。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`，Vite/TS build 成功；仍有既有 bundle >500 kB 提示。
- 已通过：重启 PC Node 到 `0.0.0.0:7001`，实际监听 PID `74521`。
- 已通过：只读 summary smoke 返回 `camera_usb_speed=12M`、`camera_usb_full_speed_detected=true`、`camera_usb_high_speed=false`、`camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_source_diagnosis_not_exclusive=true`、`camera_source_diagnosis_plain_hint` 包含 USB 12M full-speed 说明、`camera_hardware_action_required=true`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`。
- 已通过：no-motion 雷达刷新 `POST /api/robot-control/radar/scan-proof/refresh` 返回 `robot_control_executed=false`、`latest_scan_proof_fresh=true`；随后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=103`、`radar_overlay_needs_refresh=false`、`path_preview_status=path_preview_observed`；最终 summary 返回 `live_wysiwyg_missing_surface_ids=[camera]`、`radar_map_points_visible=true`、`mapping_lidar_fresh_readback_ready=true`。

## 剩余风险

- 本轮只补 PC 只读诊断 alias；真实相机仍需要把摄像头接到高速 USB 口/线或供电 Hub 后复测首帧。
- 本轮不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
