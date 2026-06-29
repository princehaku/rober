# PC Nav2 latest 与键盘连续控制读回别名

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/nav2/goal/execution/latest` 从 `goal_execution_key_values` 提升关键顶层别名：
  `goal_execution_status`、`result_status`、`nav2_goal_execution_proven`、`execution_proof_gap`、
  `goal_execution_robot_control_executed`、`goal_execution_feedback_sample_count`、
  `goal_execution_base_feedback_sample_count` 和 `goal_execution_base_feedback_nonzero_sample_count`。
  顶层 `robot_control_executed` 仍表示本次 latest 只读请求没有发车，历史执行事实留在 `goal_execution_*`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：键盘 readback 增加
  `continuous_control_ready=true`、`keyboard_control_start_ready=true` 和 `hold_to_move_required=true`，
  让 summary / keyboard_control / keyboard_teleop 三个名字都能直接表达“勾安全确认后可启用，必须按住才连续低速移动”。
- `pc-tools/workstation/src/shared/contracts.ts`：同步固定 Nav2 latest 与 keyboard readback response contract。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补齐 Nav2 latest 顶层执行事实、未证明 wheel L/R 缺口、键盘连续控制 ready 别名断言。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录最新只读字段口径；本轮不执行 Nav2、不启用键盘、不发送 manual/free-roam/delivery/stop 或 `/cmd_vel`。

## 验证结果

- `npm run build`：通过。
- `npm test -- catalog.test.ts`：通过，`167 passed`。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `git diff --check`：通过。
- 重启 PC Node：`HOST=0.0.0.0 PORT=7001 ROBOT_CONTROL_DEFAULT_BASE_URL=http://192.168.1.11:8787 npm run api`，监听 `*:7001`，PID `42435`。
- live 只读验证 `GET http://127.0.0.1:7001/api/robot-control/nav2/goal/execution/latest`：
  - `proxy_status=latest_loaded`
  - `goal_execution_status=goal_succeeded`
  - `result_status=succeeded`
  - `nav2_goal_execution_proven=false`
  - `execution_proof_gap=wheel_lr_nonzero_not_proven`
  - `goal_execution_robot_control_executed=true`
  - `robot_control_executed=false`
  - `goal_execution_feedback_sample_count=8`
  - `goal_execution_base_feedback_sample_count=239`
  - `goal_execution_base_feedback_nonzero_sample_count=0`
  - `base_command_mode=pwm`
  - `goal_execution_base_feedback_latest_raw_left=0`
  - `goal_execution_base_feedback_latest_raw_right=0`
  - 下一步提示用 ROS 模式重跑图上路线，并在同窗口确认轮速 L/R 非零。
- live 只读验证 `GET http://127.0.0.1:7001/api/robot-control/summary`：
  - `readback_summary.keyboard.continuous_control_ready=true`
  - `readback_summary.keyboard.keyboard_control_start_ready=true`
  - `readback_summary.keyboard.hold_to_move_required=true`
  - `readback_summary.keyboard_control` 同步镜像同一组字段。

## 剩余风险

- 本轮只补只读契约和脚本可读性，没有发送真实 Nav2 执行或键盘手控脉冲；完整路线仍需现场安全确认后重跑，并证明同窗口 wheel raw L/R 非零。
- 当前 live Nav2 证据仍是“路线 action succeeded，但轮速 L/R=0/0 未证明”；自动驾驶不能按完成收口。
- 摄像头仍是 UVC 无首帧，雷达 overlay 仍无新鲜点；它们不阻塞自由移动，但阻塞可验收建图。
