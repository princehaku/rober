# Radar Status Scan Refresh Guidance

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 修正 summary radar fallback：当雷达没有贴到地图且没有更具体缺口时，下一步从“先刷新雷达状态”改为“先刷新雷达扫描读数，再读取雷达状态；就绪后刷新地图画面确认雷达点”。
- `pc-tools/workstation/src/server/index.ts`
  - 同步修正 `GET /api/robot-control/radar/status` 本地回包 fallback，避免现场直接 curl radar status 时漏掉 scan-proof refresh。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 radar status stale proof 场景，断言 lifecycle running、观察项齐全但 proof 不新鲜时，PC 明确引导先刷新雷达扫描读数，而不是只刷新状态。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 radar status / summary fallback 的只读刷新顺序。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run catalog.test.ts robotControlSummary.test.ts`，2 个 test files、192 个测试通过。
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`，3 个 test files、429 个测试通过。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build 通过，仅保留既有 Vite chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，listener PID `50699`。
- 通过：live `GET http://127.0.0.1:7001/api/robot-control/summary` 在 stale 雷达贴图时返回 `radar_next_action_plain=先刷新雷达扫描读数，再读取雷达状态；就绪后刷新地图画面确认雷达点`，`live_wysiwyg_radar_map_refresh_sequence=[/api/robot-control/radar/scan-proof/refresh,/api/robot-control/radar/status,/api/robot-control/map/preview,/api/robot-control/summary]`。
- 通过：live `GET http://127.0.0.1:7001/api/robot-control/radar/status` 返回同样的 `radar_next_action_plain`，且 `readback_only=true`、`sends_motion_when_clicked=false`、`starts_radar_lifecycle=false`、`robot_control_executed=false`。
- 通过：执行只读 `POST http://127.0.0.1:7001/api/robot-control/radar/scan-proof/refresh` 返回 `readback_only=true`、`no_motion_refresh=true`、`sends_motion_when_clicked=false`、`starts_radar_lifecycle=false`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`submits_delivery=false`、`stops_motion=false`、`latest_scan_proof_fresh=true`。
- 通过：随后 live `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=153`、`radar_overlay_source_point_count=156`、`radar_overlay_refresh_required=false`、`path_preview_status=path_preview_observed`、`robot_pose_status=map_pose_observed`。
- 通过：最终 live `GET /api/robot-control/summary` 返回 `live_wysiwyg_missing_surface_ids=["camera"]`、`radar_map_points_visible=true`、`radar_overlay_status=loaded`、`mapping_start_missing_reasons=["camera_first_frame"]`、`mapping_lidar_fresh_readback_ready=true`、`mapping_lidar_fresh_gate_status=ready`。

## 剩余风险

- 本轮只修正只读 radar/status 与 summary guidance，不启动雷达 lifecycle、不执行 Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。
- 当前真实目标仍未完成：完整 Nav2 路线执行、wheel raw L/R 非零、delivery success、键盘连续手控、相机首帧、建图启动仍需继续现场验证。
