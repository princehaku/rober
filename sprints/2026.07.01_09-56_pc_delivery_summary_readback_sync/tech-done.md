# PC 送达读回同步当前卡点

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：
  - 新增 `refreshLiveDeliveryClosureReadback()`，固定先读 `/api/robot-control/delivery/latest`，再刷新 `/api/robot-control/summary`。
  - 普通首屏 `plain-live-delivery-closure-readback` 和按钮暴露 `data-readback-refresh-endpoints=/api/robot-control/delivery/latest,/api/robot-control/summary`、`data-refreshes-delivery-latest=true`、`data-refreshes-summary=true` 和 `data-summary-delivery-success`。
  - 完整行程读回 `run_nav2_route` 在读完地图、Nav2 latest、底盘轮速后，也走同一送达 + summary 收口，避免当前卡点的 delivery success 落后一拍。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：完整行程验收端点顺序改为地图、Nav2 latest、底盘轮速、delivery latest、summary，让 summary 成为最终聚合结论。
- `pc-tools/workstation/test/App.test.ts`：同步 fixture 和 DOM 合同断言。
- `docs/product/pc_tools_workstation.md`：记录送达读回同步 summary 的只读合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，7 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 仍提示既有 bundle size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `15550`；`HEAD http://127.0.0.1:7001/map` 返回 `200`。
- 通过：只读 live summary `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `wheel_rerun_acceptance_endpoints=[/api/robot-control/map/preview,/api/robot-control/nav2/goal/execution/latest,/api/robot-control/base/feedback-samples,/api/robot-control/delivery/latest,/api/robot-control/summary]`，`run_nav2_route.acceptance_plain` 明确 delivery latest 后 summary 收口；live 当前 `delivery_success=false`、`wheel_lr_nonzero_proven=false`。

## 剩余风险

- 本轮不提交送达、不执行 Nav2、不发送 manual/keyboard/free-roam/map runtime/stop 或 `/cmd_vel`。
- live 当前仍需要现场安全确认后重跑图上路线并复验同窗口 wheel L/R；delivery success 仍需现场完成送达确认后才能变为 true。
