# PC live-summary 雷达贴图短 alias

sprint_type: micro

## 实际改动

- `live_closure_summary` 和 `/api/robot-control/live-summary` 新增 `radar_overlay_*` 短 alias，直接暴露雷达贴图状态、当前点数、来源点数、主要阻塞原因和下一步只读刷新说明。
- 普通首屏 WYSIWYG 诊断 DOM 增加对应 `data-radar-overlay-*` 字段，DOM smoke 可直接判断雷达开始后地图标记是否贴到当前地图。
- 固定暴露 `fixed_radar_overlay_refresh_endpoint=/api/robot-control/radar/scan-proof/refresh` 和 `fixed_radar_overlay_map_preview_endpoint=/api/robot-control/map/preview`，并声明刷新不发车、不启动雷达 lifecycle。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "minimal precheck fields for same-window wheel rerun"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，1 passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单包 chunk 超过 500 kB，这是既有体积提醒，不影响本轮功能。
- `cd pc-tools/workstation && npm test`：通过，3 files / 418 tests。
- `git diff --check`：通过。
- 运行态只读确认：PC API 已重启到 `0.0.0.0:7001`，`GET /api/robot-control/live-summary` 返回 `radar_overlay_status=not_current`、`radar_overlay_current_point_count=0`、`radar_overlay_source_point_count=187`、`radar_overlay_primary_blocked_reason=runtime_scan_stale_for_map_radar_overlay`，并暴露只读刷新端点 `/api/robot-control/radar/scan-proof/refresh` 与 `/api/robot-control/map/preview`，`radar_overlay_refresh_sends_motion=false`、`radar_overlay_refresh_starts_radar_lifecycle=false`。

## 剩余风险

- 本轮只补可读短 alias；真实雷达贴图仍需要现场执行只读刷新扫描再刷新地图。摄像头首帧仍受 USB full-speed 硬件链路影响，轮速/delivery 也仍需现场安全确认后的执行闭环。
