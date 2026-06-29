# PC 地图雷达点当前 frame 拆分

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为地图雷达 overlay 增加 `radar_overlay_source_frame_id`、`map_marker_source_frame_id`、`RobotControlMapPreviewRadarOverlay.source_frame_id`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：把 `radar_overlay_frame_id` / `map_marker_frame_id` 修正为当前实际贴到地图的雷达点 frame；旧扫描来源 frame 单独放入 source frame 字段。`radar_overlay_scan_preview_frame_id` 仍保留来源扫描 frame。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖当前雷达点、partial overlay、stale stopped overlay 和 map preview 响应中的 frame 拆分。
- `pc-tools/README.md`：记录新的只读合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`，`166 passed`。首次运行发现 `radar_overlay_scan_preview_frame_id` 被误改成当前 frame，已修复为继续保留来源扫描 frame 后重跑通过。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`，`217 passed`。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build 成功，仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：PC Node 重启到 `0.0.0.0:7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`。
- 通过：live summary 返回 `radar_overlay_status=not_current`、`radar_overlay_point_count=0`、`radar_overlay_frame_id=not_loaded`、`radar_overlay_source_frame_id=laser_frame`、`radar_overlay_scan_preview_frame_id=laser_frame`。
- 通过：live map preview 返回 `radar_overlay_point_count=0`、`radar_overlay_frame_id=""`、`radar_overlay_source_frame_id=laser_frame`、嵌套 `radar_overlay.frame_id=""`、`radar_overlay.source_frame_id=laser_frame`。

## 剩余风险

- 本轮不启动雷达、不刷新地图、不发送 manual/keyboard/Nav2/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实雷达贴图完成仍需要现场启动雷达、等待新扫描并刷新地图画面；本轮只避免旧来源 frame 被误读成当前地图 marker。
