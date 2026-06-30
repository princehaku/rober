# PC Radar Runtime Scan Map Card Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlActionStatusCard.evidence` 新增 `map_radar_*` 和 `runtime_scan_*` 字段，用普通用户口径区分“地图上实际贴图点数”和“runtime 已读到的扫描材料”。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `radar_map_points` action card 输出地图雷达状态、实际贴图点数、来源点数、lifecycle stopped 阻断、runtime scan 状态、点数、frame、age 和来源。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-action-status-card-radar_map_points` DOM 暴露对应 `data-map-radar-*` 与 `data-runtime-scan-*` 字段。
  - 前端兼容旧 summary：如果旧 action card 缺新字段，会从 `readback_summary.radar/lidar` 或旧 `blocked_reasons/source_point_count/source_frame_id` 推导。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 锁定新 action card 字段。
  - 保留“只有压缩雷达点数时不伪造地图坐标”的测试，确保 runtime scan fresh 也不会被误贴成当前地图点。
- `docs/product/pc_tools_workstation.md`
  - 同步记录地图雷达点 action card 的 runtime scan vs 地图贴图合同。

## 验证结果

- `npm test -- test/App.test.ts -t "routes the sensor shortcut"`：通过。
- `npm test -- test/App.test.ts -t "keeps radar point count visible from lidar summary"`：通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`：通过。
- `npm test -- --run`：通过，2 个测试文件、396 个测试全部通过。
- `npm run lint`：通过，0 个 error；保留既有 4 个 Vue warning。
- `npm run build`：通过，产物包含 `dist/assets/index-DlgYS8R3.js` 与 `dist/assets/index-DCA8Xtd4.css`。
- `git diff --check`：通过。
- 7001 live 验证：
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` PID `42201` 监听 `*:7001`。
  - `curl http://127.0.0.1:7001/` 返回新资产 `/assets/index-DlgYS8R3.js` 和 `/assets/index-DCA8Xtd4.css`。
  - 打包 JS 包含 `data-map-radar-status`、`data-map-radar-blocked-by-lifecycle-not-running`、`data-runtime-scan-status`、`data-runtime-scan-point-count`、`data-runtime-scan-source`。
- 7001 live summary 验证：
  - `radar_map_points.status=not_current`。
  - `current_on_map=false`，`current_point_count=0`，`source_point_count=81`。
  - `radar_lifecycle_running=false`，`radar_lifecycle_state=stopped`。
  - `map_radar_status=not_current`，`map_radar_point_count=0`，`map_radar_source_point_count=81`，`map_radar_blocked_by_lifecycle_not_running=true`。
  - `runtime_scan_status=fresh`，`runtime_scan_fresh=true`，`runtime_scan_point_count=72`，`runtime_scan_source_point_count=81`，`runtime_scan_frame_id=laser_frame`，`runtime_scan_age_s=0.08`，`runtime_scan_source=free_roam_runtime_snapshot`。

## 剩余风险

- 本轮只补 PC Web 只读 summary/DOM 合同，不自动启动雷达、不刷新地图、不发送任何运动命令。
- live 当前仍显示雷达 lifecycle stopped、地图当前雷达点 0 个；下一轮若要把地图上实际点数变为非零，需要现场显式启动/刷新雷达并刷新地图 preview。
- ROS2 原生大图/调试视图建议使用 RViz2 或 Foxglove Studio；PC 简易界面继续面向普通用户，只承担“可看懂、可操作、可验收”的地图状态和任务入口。
