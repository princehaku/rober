# 建图入口补齐地图雷达点证据

sprint_type: micro

## 实际改动

- 普通首屏 `plain-mapping-start-gate` 新增地图雷达点 WYSIWYG 证据。
- 建图入口现在同时显示“画面/雷达 ready”和“地图雷达点是否真的显示、显示几个点”。
- 新增 DOM 字段：`data-radar-map-points-visible`、`data-radar-map-point-count`、`data-radar-map-source-point-count`、`data-fixed-radar-map-preview-endpoint`。
- 同步更新 PC 工作站 README 和产品边界文档。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "points mapping-ready users to start the map recording when only mapping runtime is missing"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "auto-refreshes radar proof after plain radar start reports ok"`，1 passed / 218 skipped。
- 通过：`npm test -- --run`，389 passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue newline warnings。
- 通过：`npm run build`，生成 `dist/assets/index-DJgw60-X.css` 和 `dist/assets/index-aFpjz8uL.js`；仅 Vite chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮仅改 PC Web 只读仪表、DOM 合同和文档，不包含真实雷达启动、真实地图预览、真实建图记录或上车 HIL 验证。
