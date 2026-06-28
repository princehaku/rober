# PC Radar Status Plain Marker Guidance

sprint_type: micro

## 实际改动

- `GET /api/robot-control/radar/status` 顶层新增雷达本体只读 alias：
  - `continuous_scan_status`
  - `lifecycle_running`
  - `lifecycle_state`
  - `latest_scan_proof_fresh`
  - `scan_point_count`
  - `latest_scan_age_ms`
- 同步新增普通用户可读白话：
  - `radar_status_plain`
  - `radar_next_action_plain`
  - `radar_overlay_point_count`
  - `radar_overlay_source_point_count`
  - `radar_overlay_wysiwyg_status_plain`
  - `radar_overlay_wysiwyg_next_action_plain`
- 合同明确区分：`radar/status` 只证明雷达本体运行和扫描 fresh；地图 marker 是否所见即所得仍以 `/api/robot-control/map/preview` 的 overlay 字段为准。
- 同步更新前端 fallback、测试 fixture、catalog 合同测试、PC tools README 和产品文档。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "radar status proxy exposes"`，结果 `Test Files 1 passed (1)`，`Tests 1 passed | 158 skipped (159)`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `Test Files 2 passed (2)`，`Tests 374 passed (374)`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 TypeScript、Vite 和 server TypeScript build 全部通过；Vite 仅保留既有 chunk size warning。
- 通过：本机 PC API 已重启到 `0.0.0.0:7001`，监听进程为 `node` PID `14040`。
- 通过：只读检查 `GET http://127.0.0.1:7001/api/robot-control/radar/status` 返回 `proxy_status=status_loaded`、`robot_control_executed=false`、`continuous_scan_status=lifecycle_not_running`、`lifecycle_running=false`、`lifecycle_state=stopped`、`latest_scan_proof_fresh=false`。
- 通过：同一 live 只读响应返回 `radar_status_plain=雷达未运行或扫描已停；旧雷达来源点不能当作当前地图 marker。`，`radar_overlay_wysiwyg_status_plain=雷达 status 不直接绘制地图 marker；雷达未运行或扫描已停；旧雷达来源点不能当作当前地图 marker。`

## 剩余风险

- 本轮只补 radar status 只读字段，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 当前 live 雷达仍显示 lifecycle stopped、latest scan proof stale；真实地图 marker 仍需要启动雷达并刷新地图预览后验证。
