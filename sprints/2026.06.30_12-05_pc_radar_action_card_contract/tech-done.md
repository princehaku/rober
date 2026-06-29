# 2026.06.30 12:05 PC Radar Action Card Contract

sprint_type: micro

## 实际改动

- `radar_map_points` action card 新增只读 evidence：`radar_lifecycle_running`、`radar_start_configured`、固定 radar start/refresh endpoint，以及 `radar_refresh_after_start_required`。
- 普通首屏 action card DOM 同步暴露 `data-radar-lifecycle-running`、`data-radar-start-configured`、`data-fixed-radar-start-endpoint`、`data-fixed-radar-refresh-endpoint`、`data-radar-refresh-after-start-required`。
- 前端兼容旧 summary：即使旧 action card 没带新 evidence，也从 `readback_summary.radar/lidar` 派生这些只读字段。
- 补充 catalog/App 定向测试，覆盖后端 summary 合同和普通首屏 DOM 合同。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "routes the sensor shortcut from structured action cards instead of camera wording"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- --run`，2 files / 389 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 与 `vite build` 通过；保留既有 bundle size warning。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `*:7001`。只读 live summary 返回 `radar_map_points.evidence.radar_lifecycle_running=false`、`radar_start_configured=true`、`fixed_radar_start_endpoint=/api/robot-control/radar/start`、`fixed_radar_refresh_endpoint=/api/robot-control/radar/scan-proof/refresh`、`radar_refresh_after_start_required=true`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补 PC summary/UI 的只读证据；真实启动雷达、刷新地图雷达点和建图验收仍需要现场显式操作与硬件状态配合。
