# PC 本轮进度主 ready 动作按钮

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“本轮进度”的“可先动”提示下方新增主 ready 动作按钮。
  - 按钮消费 `goal_checklist_summary.primary_ready_action_source_card_id`，当前 live 形态显示“去先自由移动”。
  - 点击后只滚动并聚焦到对应动作区，不勾选安全确认、不点击启动、不发送任何运动请求。
- `pc-tools/workstation/test/App.test.ts`
  - 增加普通首屏回归断言：主 ready 动作按钮会聚焦自由移动安全确认控件，且不会增加 `fetch` 请求。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏新增主 ready 动作按钮和安全边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "plain"`
  - `Test Files 1 passed (1)`，`Tests 46 passed | 171 skipped (217)`。
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`，`Tests 382 passed (382)`。
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成；Vite 仍提示既有 bundle 大小 warning。
- 通过：`git diff --check`
- 通过：7001 本地服务重启。
  - `node` 监听 `TCP *:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读 live `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - `primary_ready_action_item_id=free_move`
  - `primary_ready_action_source_card_id=free_move`
  - `ready_action_ids=free_move,keyboard_continuous_control,nav2_route_execution`
  - `camera_status=source_first_frame_failed`
  - `radar_status=radar_stopped`
  - `nav2_status=goal_succeeded_wheel_feedback_not_proven`
  - `free_roam_status=start_ready`
  - `free_move_start_ready=true`

## 剩余风险

- 本轮只新增 PC 首屏只读聚焦入口，没有现场安全确认，因此没有启动自由移动、键盘连续手控、底盘手控、Nav2、雷达或建图。
- 真实小车移动、Nav2 完整行程、camera 首帧和雷达 fresh 仍需要现场 operator 明确安全确认后继续验证。
