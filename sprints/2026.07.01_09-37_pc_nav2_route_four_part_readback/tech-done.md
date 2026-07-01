# 2026.07.01 09:37 PC Nav2 路线四段闭环读回

## sprint_type

micro

## 实际改动

- PC 当前卡点 `plain-live-trip-closure-readback` 和行程卡 `plain-trip-closure-readback` 增加 `data-route-ready`，文案按“图上路线、到点、同窗口 wheel L/R、delivery success”展示完整路线四段闭环。
- `run_nav2_route` 验收端点和轮速复验端点把 `/api/robot-control/map/preview` 放到第一项，再读 Nav2 latest、底盘轮速、summary 和 delivery latest，保证完整路线读回先确认地图路线仍所见即所得。
- `refreshLiveMotionRunbookReadback("run_nav2_route")` 在读 latest/轮速/summary/delivery 前先刷新地图预览；该链路仍只读，不执行 Nav2、不发 manual/keyboard/free-roam/stop 或 `/cmd_vel`。
- 同步更新 PC 产品文档和相关前端/summary 测试合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，`1 passed | 230 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，`7 passed`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，`3 passed / 417 passed`。
- 通过：`git diff --check`。
- 通过：PC Node 已在 `0.0.0.0:7001` 监听，`GET http://127.0.0.1:7001/map` 返回 `200 OK`。
- 通过：只读 summary smoke 返回 `route_ready_on_map=true`、`nav2_goal_succeeded=true`、`wheel_lr_nonzero_proven=false`、`needs_same_window_wheel_rerun=true`、`delivery_success=false`；`run_nav2_acceptance_endpoints` 和 `wheel_rerun_acceptance_endpoints` 均为 `/api/robot-control/map/preview`、`/api/robot-control/nav2/goal/execution/latest`、`/api/robot-control/base/feedback-samples`、`/api/robot-control/summary`、`/api/robot-control/delivery/latest`。

## 剩余风险

- 本轮只强化 PC/summary 的只读验收合同，没有真实发车；完整 Nav2 路线闭环仍需要现场勾安全确认后重跑，并读到同窗口 wheel L/R 非零与 delivery success。
