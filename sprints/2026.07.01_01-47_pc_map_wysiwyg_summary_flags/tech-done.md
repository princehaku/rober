# PC 地图所见即所得 summary 状态

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`readback_summary.map` 新增 `map_current_visible`、`path_current_visible`、`radar_overlay_current_visible` 三个只读字符串字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从地图 proof、路线点和雷达 overlay 派生上述字段，保留原 `status=not_proven` 的 proof 边界，同时让 PC 首屏和脚本能直接判断地图画面、图上路线、地图雷达点是否当前可见。
- `pc-tools/workstation/test/catalog.test.ts`：补充地图可见、路线可见、旧雷达来源点不贴当前图的断言。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts --run`，6 tests OK。
- 通过：`npm test -- test/catalog.test.ts -t "stale|map preview|图上路线" --run`，11 tests OK / 166 skipped。
- 通过：`npm test -- --run`，3 个测试文件、412 tests OK。
- 通过：`npm run build`，生成 `dist/assets/index-BoR-EUKp.js` 与 `dist/assets/index-BMxcT92A.css`；保留既有 Vite chunk size warning。
- 通过：`npm run lint`，0 error；保留既有 4 条 `vue/multiline-html-element-content-newline` warning。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后，live 只读 `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 HTTP 200，`map_current_visible=true`、`path_current_visible=true`、`radar_overlay_current_visible=false`、`path_preview_point_count=18`、`radar_overlay_point_count=0`、`radar_overlay_source_point_count=123`、`safe_to_control=false`。

## 剩余风险

- 本轮只改 PC summary 的只读 WYSIWYG 状态字段，不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 现场雷达仍是旧来源点 123 个但当前不贴图；需要刷新雷达扫描并刷新地图画面，才能把 `radar_overlay_current_visible` 提升为 `true`。
