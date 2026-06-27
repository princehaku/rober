# PC 地图旧雷达 overlay 前端兜底

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `summaryRadarOverlayNotCurrentForPlainMap()`：当 summary map overlay 声称 `loaded/partial`，但 lidar 事实显示 `runtime_scan_status=stale` 或 lifecycle stopped 时，普通地图把该 summary overlay 当成 not-current。
  - 普通地图不再从 `o3_proof_summary` 回捞 stopped/stale 的旧点数组，也不显示 `雷达局部点 ...`。
  - 只拦截 summary fallback；当前 `/api/robot-control/map/preview` 随图返回的 overlay 仍按同轮只读刷新结果显示。
- `pc-tools/workstation/test/App.test.ts`
  - 新增混合版本回归：旧 7001 返回 `map.radar_overlay_status=partial` 但 lidar stopped/stale 时，前端不画旧点、不显示 65 个局部点、不触发任何控制接口。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录前端兼容旧 7001 的 not-current 兜底规则。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --testNamePattern "not-current map radar overlay|stale stopped lidar|radar overlay summary" --maxWorkers=1 --no-fileParallelism`
  - `Test Files 1 passed | 1 skipped (2)`，`Tests 2 passed | 322 skipped (324)`
- 通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - `Test Files 2 passed (2)`，`Tests 324 passed (324)`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite 仍提示单 chunk 超过 500 kB；本轮未改变该既有打包策略。
- 通过：`git diff --check`

## 剩余风险

- 本轮修的是 PC 前端混合版本 WYSIWYG 兜底；不启动雷达、不刷新雷达、不重启 7001、不证明现场雷达当前 fresh。
- live 只读 summary 当前仍显示 `runtime_scan_status=stale`、`lifecycle_running=false`，需要现场启动/刷新雷达后才能看到当前雷达 marker。
