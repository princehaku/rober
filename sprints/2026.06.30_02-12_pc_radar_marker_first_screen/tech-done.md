# PC 首屏显示地图雷达 marker 事实

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏雷达卡片新增 `地图雷达事实` 行，直接展示 summary 中的地图 radar overlay WYSIWYG 结论和下一步。
- `pc-tools/workstation/test/App.test.ts`：补充首屏 DOM 断言，锁定普通用户能看到地图 marker 当前显示点数。
- `docs/product/pc_tools_workstation.md`：同步记录该首屏字段的只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`，结果 `1 passed | 214 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：重启 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，确认 `radar_overlay_wysiwyg_status_plain` live 返回“当前显示 0 个点；旧来源点 81 个只作诊断”，`map_marker_point_count=0`、`map_marker_source_point_count=81`；普通首屏 DOM 由测试锁定 `plain-radar-map-marker-readback` 会显示地图雷达事实。

## 剩余风险

- 当前改动只把已有雷达 marker summary 展示到普通首屏；真实 marker 更新仍依赖用户显式启动雷达、等待 fresh scan 并刷新地图画面。
