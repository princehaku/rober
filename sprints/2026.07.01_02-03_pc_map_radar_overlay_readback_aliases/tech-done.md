# PC Map Radar Overlay Readback Aliases Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlMapPreviewRadarOverlay`、`RobotControlMapPreviewResponse` 和 `readback_summary.map` 增加雷达贴图 freshness/旧点抑制字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 复用现有地图雷达 overlay 判断，新增：
    - `radar_overlay_refresh_required`
    - `radar_overlay_stale_source_points_suppressed`
    - `radar_overlay_primary_blocked_reason`
    - `radar_overlay_current_vs_source_plain`
  - 字段同时出现在 summary map 区块、map preview 顶层和嵌套 `radar_overlay`，口径一致。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 覆盖 loaded、not_loaded、not_current/stale 雷达贴图场景，锁定“旧来源点不贴当前地图”和“只读字段直接说明下一步”的合同。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`
  - 同步记录地图雷达贴图只读别名合同。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts --run`，6 tests OK。
- 通过：`npm test -- test/catalog.test.ts -t "map preview|stale|雷达" --run`，11 tests OK / 166 skipped。
- 通过：`npm test -- test/App.test.ts -t "radar overlay|map preview|direct map" --run`，19 tests OK / 210 skipped。
- 通过：`npm test -- --run`，3 files / 412 tests OK。
- 通过：`npm run build`。
- 通过：`npm run lint`，0 errors / 4 warnings（Vue 模板换行 warning，未阻塞）。
- 通过：`git diff --check`。
- 通过：PC Node 重启到 `0.0.0.0:7001`，PID `53461`。
- 通过：live 只读 GET `/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：
  - `readback_summary.map.radar_overlay_refresh_required=true`
  - `readback_summary.map.radar_overlay_stale_source_points_suppressed=true`
  - `readback_summary.map.radar_overlay_primary_blocked_reason=runtime_scan_stale_for_map_radar_overlay`
  - `readback_summary.map.radar_overlay_current_vs_source_plain=地图雷达点：当前 0 个，来源 123 个；旧来源点已抑制，未贴到当前地图；下一步：刷新雷达扫描，再刷新地图画面。`
- 通过：live 只读 GET `/api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 顶层与嵌套 `radar_overlay` 均返回同一组 refresh/stale/source/plain 字段。
- 通过：`GET /map` 返回 HTTP 200，确认地图大屏入口存在。

## 剩余风险

- 本轮只补只读合同和 UI/脚本可读性；没有刷新真实雷达 scan proof，也没有启动雷达 lifecycle。
- 真实现场当前仍需要 fresh scan proof 才能把雷达点贴到地图；旧来源点会继续被抑制，不能冒充当前所见。
- 地图太小的普通用户入口仍优先使用 PC `/map` 直达大屏；RViz2 和 Foxglove 只作为 ROS2 工程调试/远程观察配套，不是发车或手控前置。
