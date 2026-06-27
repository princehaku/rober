# PC Map Radar Overlay Current Summary

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.map.radar_overlay_*` 不再无条件复用旧 `o3_proof_summary.scan_preview_*` 点数。
  - 当 LiDAR runtime `/scan` 已 `stale` 或雷达 lifecycle 已 `stopped` 时，地图 overlay 状态改为 `not_current`，`radar_overlay_scan_preview_point_count=0`，blocked reasons 写明 `runtime_scan_stale_for_map_radar_overlay` / `radar_lifecycle_not_running_for_map_radar_overlay`。
  - `o3_proof_summary.scan_preview_point_count` 和 `readback_summary.lidar.scan_preview_*` 仍保留旧材料诊断，不把诊断材料当成当前地图标记。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 live 形态回归：旧 scan proof 有点数、free-roam runtime scan stale、radar lifecycle stopped 时，map overlay 点数必须归零。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 summary 合同层面的雷达地图所见即所得口径。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "stale stopped radar proof" --maxWorkers=1 --no-fileParallelism`
  - `Tests 1 passed | 321 skipped (322)`。
- 已通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - `Test Files 2 passed (2)`，`Tests 322 passed (322)`。
- 已通过：`cd pc-tools/workstation && npm run lint`
  - 无 ESLint 报错。
- 已通过：`cd pc-tools/workstation && npm run build`
  - `vite build` 完成；保留既有 chunk size warning。
- 已通过：`git diff --check`
  - 无空白错误。

## 剩余风险

- 本轮只修 PC summary 合同，不启动雷达、不刷新 proof、不执行 Nav2、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel`。
- 当前 live 上位机的旧 scan proof 点数仍会作为诊断材料保留；要恢复当前地图 overlay，仍需现场启动/刷新雷达并拿到 fresh runtime scan。
