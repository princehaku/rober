# 2026.06.30 13:50 PC 建图端点合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `free_move` / `mapping_start` action card evidence 新增固定建图记录和地图画面验收端点。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 后端 summary 为自由移动卡和建图启动卡固定返回 `/api/robot-control/map/start` 与 `/api/robot-control/map/preview`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 前端兼容旧 summary，自动派生同一份建图端点合同。
  - 普通首屏 action card DOM 暴露 `data-fixed-mapping-start-endpoint` / `data-fixed-mapping-preview-endpoint`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 补后端 action card 和前端 DOM 断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录建图记录入口、地图画面验收入口和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 169 skipped (170)`。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite build 成功；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读检查 `GET /api/robot-control/summary`。
  - `mapping_start.evidence.fixed_mapping_start_endpoint=/api/robot-control/map/start`。
  - `mapping_start.evidence.fixed_mapping_preview_endpoint=/api/robot-control/map/preview`。
  - `free_move.evidence.fixed_mapping_start_endpoint=/api/robot-control/map/start`。
  - `free_move.evidence.fixed_mapping_preview_endpoint=/api/robot-control/map/preview`。
  - `robot_control_executed=false`。

## 剩余风险

- 本轮只补只读合同和 DOM evidence，不自动启动建图、不启动自由移动、不发送 manual/keyboard/Nav2/free-roam/delivery/stop 或 `/cmd_vel`。
- live 当前建图仍缺 `lidar_fresh`；需要现场启动雷达并刷新同轮地图画面后，才能让建图启动从 `not_ready` 变成 `ready`。
