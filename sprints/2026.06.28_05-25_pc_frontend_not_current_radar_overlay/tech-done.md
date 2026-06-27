# PC Frontend Not-current Radar Overlay

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通地图的雷达 readback 现在会消费 `readback_summary.map.radar_overlay_status=not_current`。
  - 当 summary 明确 stopped/stale 雷达不能作为当前地图 overlay 时，前端不再从 `o3_proof_summary.scan_preview_points` 或 `readback_summary.lidar.scan_preview_point_count` 回捞旧点数组/点数画局部点云。
  - map preview 自身若返回同轮 `loaded/partial` overlay，仍优先使用，因为它是随当前地图画面一起返回的只读数据。
- `pc-tools/workstation/test/App.test.ts`
  - 新增普通首屏回归：旧 proof 仍有点数组和 65 点材料，但 summary 标记 `radar_overlay_status=not_current` 时，地图不显示雷达局部点云，也不会把旧点数写成当前雷达标记。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 UI 已消费 `not_current` summary 合同。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "not-current map radar overlay" --maxWorkers=1 --no-fileParallelism`
  - `Tests 1 passed | 322 skipped (323)`。
- 已通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - `Test Files 2 passed (2)`，`Tests 323 passed (323)`。
- 已通过：`cd pc-tools/workstation && npm run lint`
  - 无 ESLint 报错。
- 已通过：`cd pc-tools/workstation && npm run build`
  - `vite build` 完成；保留既有 chunk size warning。
- 已通过：`git diff --check`
  - 无空白错误。

## 剩余风险

- 本轮只修 PC 前端地图展示，不启动雷达、不刷新 proof、不执行 Nav2、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel`。
- 旧雷达材料仍会保留在 summary 诊断和高级区；普通地图要恢复点云，仍需要同轮 fresh radar runtime 或 map preview overlay。
