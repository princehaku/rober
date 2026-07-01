# Summary Motion Completion Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增行程/自由移动完成度短 alias：`nav2_complete`、`route_complete`、`trip_complete`、`free_move_ready`、`free_move_running` 和 `free_move_complete`。
- `nav2_complete` 镜像 `nav2_goal_execution_proven`，只表示 Nav2 action 到点成功读回；`route_complete` / `trip_complete` 跟随 `run_nav2_route` runbook 的完整验收，不会把缺 wheel L/R 或 delivery success 的行程误报为完成。
- `free_move_ready` 镜像 `free_move_start_ready`，`free_move_running` 镜像 `free_roam_motion_ready`，`free_move_complete` 跟随 `start_free_move` runbook 的验收完成状态。
- 更新 summary 合同、服务端返回、定向测试、catalog live-summary 合同测试和 PC 工作站产品文档。

## 验证结果

- 通过：`git diff --check`
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，结果 `1 passed / 9 passed`。
- 通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，结果 `1 passed / 1 passed / 180 skipped`。
- 通过：`npm test`，结果 `3 passed / 421 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001` 后，用只读 `GET /api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 确认行程/自由移动完成度短 alias 不再为 `null`：`nav2_complete=true`、`route_complete=false`、`trip_complete=false`、`free_move_ready=true`、`free_move_running=false`、`free_move_complete=false`。

## 剩余风险

- 本轮只增加只读 alias，不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 当前真实状态仍是 `route_complete=false`、`trip_complete=false`、`free_move_complete=false`；需要现场勾安全确认后复验 wheel L/R、delivery success 和自由移动运行读数。
