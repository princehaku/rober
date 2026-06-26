# PC 地图雷达点数所见即所得

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plainRadarPointHint` 改为使用 `effectiveLidarReadback`，让最新 `/api/robot-control/radar/status` 覆盖旧 summary 点数。
  - 地图雷达 marker 增加“仅点数”短标签：当最新 radar/status 有 `scan_preview_point_count` 但没有点数组时，marker 显示 `待刷新雷达点 N 个` 或 `雷达点 N 个`。
  - 雷达 freshness 和坐标口径优先展示最新点数；只有没有点数/点数组时才退回自动扫图 gate 的“最近障碍距离”。
  - 保持 WYSIWYG 边界：仅点数不能冒充已贴图点数组，文案明确“仅点数，没有点数组，未贴到地图/未显示局部轮廓”。
- `pc-tools/workstation/test/App.test.ts`
  - 更新地图刷新顺带读取 radar/status 的用例，覆盖最新 status 返回 42 个雷达点但无点数组时，地图 marker、aria、freshness 和坐标口径都显示点数，而不是旧障碍距离 fallback。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 radar/status 点数优先的 PC 所见即所得口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "latest read-only radar status during map preview refresh"`
  - 通过：1 个地图/雷达 WYSIWYG 用例通过。
- `cd pc-tools/workstation && npm test`
  - 通过：2 个测试文件，255 个用例通过。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
  - 仍有 Vite 既有 chunk 大小提示：`dist/assets/index-*.js` 超过 500 kB；不影响本轮改动。

## 剩余风险

- 本轮只保证 PC 地图 marker 消费最新 radar/status 点数；如果上车端不返回点数组，PC 仍不能把点贴到地图坐标。
- 真实雷达开始后的地图点位 HIL 仍需要上车端同时提供 robot map pose、map preview 和 scan preview points 才能验收。
