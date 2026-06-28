# PC Map Preview Radar Count Aliases

sprint_type: micro

## 实际改动

- `GET /api/robot-control/map/preview` 顶层新增与 summary 同名的雷达数值 alias：
  - `radar_overlay_point_count`
  - `radar_overlay_source_point_count`
  - `radar_overlay_scan_preview_point_count`
  - `radar_overlay_scan_preview_source_point_count`
- 这些字段直接复用同轮 `radar_overlay.count/source_count/scan_preview_*`，让外部脚本只读 map preview 时也能一眼判断当前地图实际画出的雷达 marker 数和旧来源点诊断数。
- 同步更新前端测试 fixture、catalog 合同测试、PC tools README 和产品文档。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map preview"`，结果 `Test Files 1 passed (1)`，`Tests 2 passed | 156 skipped (158)`。
- 第一轮全量测试失败：`npm --prefix pc-tools/workstation test` 中 11 个 App 路线标签用例把路线总数从 `3/15` 或 `3/36` 误读成 `3/3`。根因是本轮补前端 fixture 时把 `path_preview_source_point_count` 写成 `0`，覆盖了 summary 里的完整路线 source 总数。
- 已修复：将 fixture 的 `path_preview_source_point_count` 改回 `null`，表示 map preview fixture 未提供 source 总数时由 summary 兜底。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "route|map preview|visible route|trip"`，结果 `Test Files 1 passed (1)`，`Tests 53 passed | 162 skipped (215)`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `Test Files 2 passed (2)`，`Tests 373 passed (373)`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 TypeScript、Vite 和 server TypeScript build 全部通过；Vite 仅保留既有 chunk size warning。
- 通过：本机 PC API 已重启到 `0.0.0.0:7001`，监听进程为 `node` PID `7412`。
- 通过：只读检查 `GET http://127.0.0.1:7001/api/robot-control/map/preview` 返回 `proxy_status=preview_forwarded`、`robot_control_executed=false`、`radar_overlay_point_count=0`、`radar_overlay_source_point_count=81`、`radar_overlay_scan_preview_point_count=0`、`radar_overlay_scan_preview_source_point_count=81`、`radar_overlay_frame_id=laser_frame`。

## 剩余风险

- 本轮只补 map preview 只读 alias，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 当前 live 雷达状态仍显示 lifecycle 未运行、扫描过期；这次只让“地图上实际显示 0 个 marker、旧来源点只作诊断”的事实更容易直接读取。
