# 建图雷达 fresh 未证明文案修正

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 修正 `mapping_lidar_fresh_next_action_plain` 派生逻辑：只有 `mapping_lidar_fresh_readback_ready=true` 时才输出“雷达新鲜 gate 已满足”。
  - 当 gate 不是显式 missing、但同轮读回也未证明 fresh 时，输出“建图雷达新鲜读回尚未证明”，并要求只读刷新雷达扫描、读取雷达状态、刷新 summary。
  - 该改动只改变只读 summary 文案，不启动雷达 lifecycle、建图 runtime、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加 `not_loaded` 场景断言，防止 `readback_ready=false` 时误报 gate 已满足。
- `docs/product/pc_tools_workstation.md`
  - 同步 `mapping_lidar_fresh_gate_status` 与下一步文案的合同。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，9 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "live-summary"`，1 file passed，1 passed / 180 skipped。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，421 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`，Vite/TS build 成功；仍有既有 bundle >500 kB 提示。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，实际监听 PID `45475`。
- 通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 在刷新前返回 `mapping_lidar_fresh_readback_ready=false`、`mapping_lidar_fresh_gate_status=missing`、`mapping_lidar_fresh_next_action_plain=建图启动仍缺雷达新鲜读数；先只读刷新雷达扫描并读取雷达状态，再刷新 summary。`、`radar_overlay_status=not_current`、`radar_overlay_current_point_count=0`。
- 通过：no-motion `POST http://127.0.0.1:7001/api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787` 返回 `robot_control_executed=false`、`latest_scan_proof_fresh=true`。
- 通过：no-motion `GET http://127.0.0.1:7001/api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回 `robot_control_executed=false`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=150`、`radar_overlay_source_point_count=154`、`radar_overlay_needs_refresh=false`、`path_preview_status=path_preview_observed`、`path_preview_point_count=18`。
- 通过：刷新后只读 summary 返回 `mapping_lidar_fresh_readback_ready=true`、`mapping_lidar_fresh_gate_status=ready`、`mapping_start_missing_reasons=[camera_first_frame]`、`live_wysiwyg_missing_surface_ids=[camera]`、`radar_map_points_visible=true`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=150`。

## 剩余风险

- 本轮不执行任何会让车移动的接口；完整 Nav2、键盘连续手控、自由移动和 delivery success 仍需现场安全确认。
- 真实雷达贴图已通过 no-motion 刷新恢复到当前地图可见；相机仍显示 USB full-speed / camera_first_frame 缺口，建图启动仍只差相机首帧。
