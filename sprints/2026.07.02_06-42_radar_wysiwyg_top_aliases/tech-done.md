# 雷达贴图 WYSIWYG 顶层 alias

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增 `live_wysiwyg_radar_map_*` alias：
  - `live_wysiwyg_radar_map_overlay_status`
  - `live_wysiwyg_radar_map_current_point_count`
  - `live_wysiwyg_radar_map_source_point_count`
  - `live_wysiwyg_radar_map_stale_source_points_suppressed`
  - `live_wysiwyg_radar_map_primary_blocked_reason`
  - `live_wysiwyg_radar_map_current_vs_source_plain`
  - `live_wysiwyg_radar_map_refresh_next_action_plain`
  - `live_wysiwyg_radar_map_refresh_sequence`
  - `live_wysiwyg_radar_map_refresh_sequence_labels`
- 这些字段直接复用 `live_closure_summary` 同名字段，不重算第二套雷达贴图状态；现场 `curl | jq` 不用再钻 nested 或只读兼容 `radar_overlay_*` 名称。
- 同步更新 TypeScript contracts、summary 单测和 PC workstation 产品合同。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：通过，3 files / 428 tests passed。
- `npm run lint`：通过。
- `git diff --check`：通过。
- `npm run build`：通过，Vite 仅保留既有 bundle size warning。
- 7001 已重启并监听 `*:7001`。
- `curl http://127.0.0.1:7001/api/robot-control/summary` 只读 smoke：顶层 `live_wysiwyg_radar_map_overlay_status=not_current`、`current_point_count=0`、`source_point_count=155`、`stale_source_points_suppressed=true`、`primary_blocked_reason=runtime_scan_stale_for_map_radar_overlay`，且 `live_wysiwyg_radar_map_current_vs_source_plain` 与 `live_closure_summary` 同源。
- Chrome headless DOM smoke：`plain-field-acceptance-radar-map-proof` 显示“当前 0 个，来源 155 个；旧来源点已抑制，未贴到当前地图”，并保持 `data-sends-motion-when-clicked=false`、`data-starts-radar-lifecycle=false`。

## 剩余风险

- 本轮只补只读 alias 和可见证据，没有刷新雷达 proof、没有启动雷达 lifecycle，也没有发送任何 Nav2/manual/keyboard/free-roam/建图/stop 或 `/cmd_vel`。
- 当前雷达贴图仍未完成：来源点 155 个被判定为旧点，当前地图雷达点为 0；需要现场点击只读“刷新当前所见”后复验同轮 scan proof 和地图预览。
- 相机仍提示 USB 12M full-speed，建图启动仍缺 `camera_first_frame`。
