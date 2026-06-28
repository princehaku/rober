# PC 地图 plain_hint 使用普通雷达口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增普通地图雷达句合成函数，让 `readback_summary.map.plain_hint` 和 `GET /api/robot-control/map/preview` 顶层 `plain_hint` 使用“地图雷达点 / 旧来源点只作诊断 / 原因”口径，不再直接拼高级 `雷达 marker` 文案。
- `pc-tools/workstation/test/catalog.test.ts`：补充 summary 与 map preview 契约断言，锁定普通 `plain_hint` 不含 `雷达 marker` / `overlay`；同时保留嵌套 `radar_overlay.wysiwyg_status_plain` 的精确诊断断言。
- `docs/product/pc_tools_workstation.md`：同步记录普通字段与高级诊断字段的边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary|map preview"`，结果 `1 passed`、`40 passed | 120 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：重启 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，live 返回 `readback_summary.map.plain_hint` 为“地图画面、图上路线和小车位置已显示。图上路线已显示在当前地图画面。地图雷达点当前显示 0 个，旧来源点 81 个只作诊断；原因：雷达扫描已过期、雷达未运行。下一步：先启动雷达，再刷新地图画面。”，且 `marker_in_map=false`、`overlay_in_map=false`。
- 通过：只读请求 `GET /api/robot-control/map/preview`，live 返回顶层 `plain_hint` 为“地图画面、图上路线和小车位置已显示；地图雷达点当前显示 0 个，旧来源点 81 个只作诊断；原因：雷达扫描已过期、雷达未运行。”，且 `marker_in_plain=false`、`overlay_in_plain=false`；嵌套 `radar_overlay_wysiwyg_status_plain` 仍保留精确 marker 诊断字段。

## 剩余风险

- 当前改动只调整普通只读文案合成；真实雷达启动、地图刷新、Nav2 路线复验和建图验收仍需要现场用户显式操作。
