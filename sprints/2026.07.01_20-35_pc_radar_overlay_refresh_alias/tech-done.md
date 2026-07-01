# PC 雷达贴图刷新 alias

sprint_type: micro

## 实际改动

- `live_closure_summary` / `/api/robot-control/live-summary` 增加 `radar_overlay_needs_refresh`、`radar_overlay_blocks_wysiwyg`、`radar_overlay_blocks_free_move=false` 和 `radar_overlay_recovery_sequence`，让现场脚本直接判断雷达贴图是否只需 no-motion 刷新。
- 普通首屏 WYSIWYG 诊断 DOM 同步暴露这些短字段。
- 本轮使用 no-motion 雷达刷新链路恢复运行态雷达贴图，不启动雷达 lifecycle 或任何运动入口。

## 验证结果

- no-motion 现场恢复：`POST /api/robot-control/radar/scan-proof/refresh` 返回 `proxy_status=refresh_forwarded`、`robot_control_executed=false`。
- 恢复后只读 `/api/robot-control/live-summary`：`radar_overlay_status=loaded`、`radar_overlay_current_point_count=8`、`radar_overlay_source_point_count=20`、`radar_map_points_visible=true`、`live_wysiwyg_missing_surface_ids=["camera"]`。
- `npm test -- --run test/robotControlSummary.test.ts -t "does not draw stale radar scan proof points|uses map preview embedded radar overlay"`：通过，2 passed。
- `npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，1 passed。
- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 passed。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仍提示既有 bundle size warning。
- `npm test`：通过，3 files / 418 tests passed。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001` 后只读 curl：`radar_overlay_needs_refresh=false`、`radar_overlay_blocks_wysiwyg=false`、`radar_overlay_blocks_free_move=false`、`radar_overlay_recovery_sequence=["/api/robot-control/radar/scan-proof/refresh","/api/robot-control/map/preview"]`、`radar_overlay_refresh_sends_motion=false`、`radar_overlay_refresh_starts_radar_lifecycle=false`。

## 剩余风险

- 当前地图、路线、雷达贴图已 WYSIWYG，但画面仍未 WYSIWYG：`camera_current_visible=false`。
- 建图门禁仍未 ready；重启后读到 `mapping_start_missing_reasons=["camera_first_frame","lidar_fresh"]`。这说明“地图上的雷达贴图可见”和“建图 gate 的 lidar fresh”仍是两个读回条件，后续需要单独收口 lidar fresh gate。
