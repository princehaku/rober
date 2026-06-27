# PC Partial Overlay Local Scan Regression Micro Sprint

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/test/App.test.ts`
  - 增加 partial `map_preview.radar_overlay` 前端回归：有雷达点、无 map-frame `robot_pose` 时，普通地图只显示局部雷达轮廓，不显示地图坐标雷达点 SVG 或小车 marker。
  - 断言坐标口径写明 `TF 已观察，AMCL 坐标未读到`，雷达只显示车身局部轮廓且不贴到地图。
  - 断言该只读显示路径不会调用 radar start、manual、Nav2 execute 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 partial overlay 的前端所见即所得行为。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- test/App.test.ts --testNamePattern "partial map preview radar overlay"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 178 skipped (179)`
- 已通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 312 passed (312)`
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - Vite 保留既有 chunk size warning，构建成功。
- 已通过：`git diff --check`

## 剩余风险

- 本轮只补前端回归测试和产品文档，没有修复真实 AMCL/map pose 缺失。
- 当前 live 仍是地图图片和雷达点可见，但 `robot_pose=null`，因此雷达只能按局部轮廓解释，不能按已贴地图坐标收口。
