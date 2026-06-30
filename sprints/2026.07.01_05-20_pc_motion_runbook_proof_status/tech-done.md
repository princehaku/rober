# PC 动作清单验收证据状态

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `live_motion_runbook_items` 每项新增 `completed`、`proof_status`、`missing_evidence`、`proof_plain`。
  - 完整 Nav2 行程验收链路加入 `delivery/latest`，并把缺口结构化为 Nav2 到点、同窗口 wheel L/R 非零、delivery success。
  - 键盘连续手控、自由移动、建图分别暴露按住同窗口轮速/松开 stop、free-roam latest、相机首帧/雷达新鲜等缺口。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏动作清单每行暴露 `data-completed`、`data-proof-status`、`data-missing-evidence`、`data-proof-plain`，可见状态从“可做”细化为“可验证/已完成/未就绪”。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 runbook item 类型合同。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖 motion runbook 的结构化验收证据、delivery latest endpoint 和 DOM 字段。
- `docs/product/pc_tools_workstation.md`
  - 同步记录动作清单验收证据合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts test/App.test.ts -t "same-window wheel|plain-live-motion-runbook|plain-live-closure"`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test -- --run`，结果 `Test Files 3 passed (3)`、`Tests 413 passed (413)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。
- 通过：重启 `PORT=7001 HOST=0.0.0.0 npm run api` 后只读 `GET http://127.0.0.1:7001/api/robot-control/summary` smoke：
  - `source_base_url=http://192.168.1.11:8787`
  - `status=needs_wheel_rerun`
  - `objective_done=1/4`
  - `live_motion_runbook_primary_action_id=run_nav2_route`
  - `live_motion_runbook_acceptance_endpoints=[/api/robot-control/nav2/goal/execution/latest,/api/robot-control/base/feedback-samples,/api/robot-control/summary,/api/robot-control/delivery/latest,/api/robot-control/free-roam/autonomy/latest,/api/robot-control/map/preview]`
  - `run_nav2_route.proof_status=ready_to_verify`，缺 `same_window_wheel_lr_nonzero,delivery_success`
  - `hold_keyboard.proof_status=ready_to_verify`，缺 `same_hold_window_wheel_lr_nonzero,stop_after_release`
  - `start_free_move.proof_status=ready_to_verify`，缺 `free_roam_latest_motion_ready`
  - `start_mapping_when_sensors_ready.proof_status=blocked`，缺 `camera_first_frame`

## 剩余风险

- 本轮只改 PC 只读 summary/DOM/文案，不实际执行 Nav2、键盘、自由移动或建图。
- 当前真实现场仍缺同窗口 wheel L/R 非零、键盘按住窗口轮速、free-roam latest 运行证据、相机首帧和建图条件；需要现场安全确认后才能做运动验证。
