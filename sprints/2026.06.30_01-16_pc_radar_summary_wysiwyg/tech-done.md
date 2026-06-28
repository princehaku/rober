# PC 雷达 marker summary 所见即所得入口

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 Robot Control summary 增加 `readback_summary.radar` 合同，稳定暴露雷达本体状态和地图 marker 读数。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `radarSummaryFromReadbacks`，从既有 lidar/map 摘要派生雷达 WYSIWYG 结论；不新增 Robot API 请求，也不触发雷达 start、地图 refresh 或任何车控动作。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补充 summary/fixture 对新字段的覆盖。
- `docs/product/pc_tools_workstation.md`：记录新 readback 字段的只读语义和控制边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies"`，结果 `1 passed | 159 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：重启 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，确认 `readback_summary.radar.status=radar_stopped`、`map_marker_point_count=0`、`radar_overlay_point_count=0`、`map_marker_source_point_count=81`，即旧来源点只作诊断，不当成当前地图 marker。

## 剩余风险

- 当前改动只补齐 PC summary 的雷达 WYSIWYG 只读入口；真实雷达启动、地图刷新和上车建图仍需现场安全确认与用户显式操作。
