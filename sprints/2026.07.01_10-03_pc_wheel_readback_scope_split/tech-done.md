# PC 共享轮速读回按动作分流

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：
  - `plain-live-wheel-feedback-readback` 根据受影响动作选择读回链路。
  - 若包含完整行程 `run_nav2_route` 缺口，读回按钮走地图、Nav2 latest、底盘反馈、delivery latest、summary 的完整验收链路。
  - 只有单独键盘缺口时，才继续走底盘反馈、summary 的键盘读回链路。
  - DOM 新增 `data-primary-action-id`、`data-wheel-readback-scope`、`data-wheel-readback-scope-plain`、`data-nav2-same-window-required`、`data-keyboard-hold-window-required`。
- `pc-tools/workstation/test/App.test.ts`：补充共享轮速读回 DOM 和点击行为断言，证明它只读完整验收端点，不执行 Nav2 goal、manual、free-roam、map start、delivery complete 或 stop。
- `docs/product/pc_tools_workstation.md`：同步共享轮速读回按动作分流的 PC 普通首屏合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，7 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 仍提示既有 bundle size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `29065`；`HEAD http://127.0.0.1:7001/map` 返回 `200`。
- 通过：只读 live summary `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `wheel_rerun_acceptance_endpoints=[/api/robot-control/map/preview,/api/robot-control/nav2/goal/execution/latest,/api/robot-control/base/feedback-samples,/api/robot-control/delivery/latest,/api/robot-control/summary]`、`live_motion_runbook_primary_action_id=run_nav2_route`、`keyboard_continuous_control_ready=true`、`wheel_lr_nonzero_proven=false`。

## 剩余风险

- 本轮不执行真实路线、不启用键盘、不发送任何运动命令。
- live 当前仍需要现场安全确认后重跑图上路线，才能把同窗口 Nav2 轮速 L/R 从 `0/0` 变为非零证据。
