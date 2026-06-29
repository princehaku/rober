# 2026.06.30 14:10 PC 雷达地图点验收合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `radar_map_points` action card evidence 新增固定地图预览端点和地图雷达点验收条件字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 后端 summary 为雷达贴图卡固定返回 `/api/robot-control/map/preview`，并声明必须看到地图雷达点已加载且点数大于 0 才算贴到当前地图。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 前端兼容旧 summary，自动派生同一份雷达贴图验收合同。
  - 普通首屏 action card DOM 暴露 `data-fixed-radar-map-preview-endpoint`、`data-radar-map-points-loaded-required` 和 `data-radar-map-point-count-gt-zero-required`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 补后端 action card 和前端 DOM 断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录雷达开始后必须以同轮地图预览里的地图雷达点作为所见即所得验收。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 169 skipped (170)`。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "routes the sensor shortcut from structured action cards instead of camera wording"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite build 成功；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读检查 `GET /api/robot-control/summary`。
  - `radar_map_points.evidence.fixed_radar_map_preview_endpoint=/api/robot-control/map/preview`。
  - `radar_map_points.evidence.radar_map_points_loaded_required=true`。
  - `radar_map_points.evidence.radar_map_point_count_gt_zero_required=true`。
  - `action_status_cards[]` JSON 不包含 `overlay`。
  - `robot_control_executed=false`。

## 剩余风险

- 本轮只补只读合同和 DOM evidence，不启动雷达、不刷新地图、不执行 Nav2/manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- live 当前雷达 lifecycle 未运行，地图雷达点仍是 `not_current`；需要现场启动雷达并刷新同轮地图画面后，才能用地图雷达点已加载且点数大于 0 闭合。
