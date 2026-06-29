# 2026.06.29 19:09 PC map radar next action WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 地图雷达 overlay `not_loaded` 分支现在会识别 `radar_lifecycle_not_running_for_map_radar_overlay`、`runtime_scan_stale_for_map_radar_overlay` 和 `scan_preview_points_missing`。
  - 当 live 地图雷达点为 0 且雷达未运行/扫描过期时，`radar_overlay_next_action_plain` 指向“启动雷达并等待新扫描/刷新雷达扫描后再刷新地图画面”，不再误导成“确认小车地址可访问”。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录地图雷达 marker 所见即所得下一步口径。

## 验证结果

- 已通过：`npm run build`（`pc-tools/workstation`）
  - 结果：TypeScript app/server build 与 Vite build 通过；仅保留既有 chunk-size warning。
- 已通过：`npm test -- App.test.ts`（`pc-tools/workstation`）
  - 结果：`Test Files 1 passed (1)`，`Tests 218 passed (218)`。
- 已通过：`git diff --check`
- 已重启本机 PC Node：
  - `HOST=0.0.0.0 PORT=7001 npm run api`
  - live `GET http://127.0.0.1:7001/api/robot-control/summary` 摘要：
    `radar_overlay_status=not_loaded`、`radar_overlay_next_action=start_radar_then_refresh_map_preview`、
    `radar_overlay_next_action_plain=先启动雷达并等待新扫描，再刷新地图画面确认雷达点。`

## 剩余风险

- 本轮只修 PC summary 文案，不自动启动雷达或刷新地图。
- live 雷达仍未运行，地图雷达点仍为 0；需要现场显式启动雷达并刷新地图后，才能证明地图 marker 已贴到当前地图。
