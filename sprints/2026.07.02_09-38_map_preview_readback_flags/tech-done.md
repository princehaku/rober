# Map Preview Readback Flags

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlMapPreviewResponse` 新增 `readback_only`、`map_preview_readback_only`、`no_motion_refresh` 和完整 `sends_motion_when_clicked/starts_*/submits_delivery/stops_motion` 只读边界字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `MAP_PREVIEW_READBACK_ONLY_FLAGS`，成功、失败和 blocked 的 `/api/robot-control/map/preview` 回包都统一带同一组只读/no-motion 字段。
- `pc-tools/workstation/test/catalog.test.ts`
  - 扩展固定 map preview 代理测试，断言刷新地图画面不发车、不启动雷达 lifecycle、Nav2、manual、keyboard、free-roam、建图 runtime、delivery 或 stop。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 扩展 `buildMapPreviewProxy()` 测试，确认直接调用 map preview 也能读到同一组只读/no-motion 字段。
- `docs/product/pc_tools_workstation.md`
  - 同步记录地图画面刷新只是只读证据刷新，不能被现场脚本误读成任何发车或 runtime 开关。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run catalog.test.ts robotControlSummary.test.ts`，2 个 test files、191 个测试通过。
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`，3 个 test files、428 个测试通过。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build 通过，仅保留既有 Vite chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，listener PID `27024`。
- 通过：live `GET http://127.0.0.1:7001/api/robot-control/map/preview` 返回 `proxy_status=preview_forwarded`、`readback_only=true`、`map_preview_readback_only=true`、`no_motion_refresh=true`、`sends_motion_when_clicked=false`、`starts_radar_lifecycle=false`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`submits_delivery=false`、`stops_motion=false`、`robot_control_executed=false`。
- 通过：同轮 live map preview 显示 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=6`、`radar_overlay_source_point_count=12`、`path_preview_status=path_preview_observed`、`path_preview_point_count=18`、`robot_pose_status=map_pose_observed`。
- 通过：live `GET http://127.0.0.1:7001/api/robot-control/summary` 显示 `live_wysiwyg_missing_surface_ids=["camera"]`、`radar_map_points_visible=true`、`mapping_start_missing_reasons=["camera_first_frame"]`、`current_motion_action_same_window_wheel_lr_nonzero=false`、`current_motion_action_delivery_success=false`、`keyboard_continuous_ready=true`、`keyboard_continuous_motion_verified=false`。

## 剩余风险

- 本轮只补齐地图预览只读/no-motion 合同，不执行 Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。
- 完整目标仍未完成：真实完整 Nav2 路线执行、wheel raw L/R 非零、delivery success、PC 键盘连续手控、相机首帧和真实建图启动仍需要继续按现场安全确认链路验证。
