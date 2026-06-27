# PC Nav2 复验下一步显性化

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增新鲜但未闭环 Nav2 证据的统一取值和提示函数。
  - 普通首屏在 `goal_succeeded + feedback + wheel raw L/R 未非零证明` 时，不再只显示泛化的“重新执行行程”，而是提示“重新执行/下次用 ros 重新执行这条图上路线，并确认执行窗口 wheel raw L/R 非零”。
  - 行程状态在存在新鲜未闭环证据时优先显示底盘反馈诊断；无诊断证据时仍保持安全确认优先。
- `pc-tools/workstation/test/App.test.ts`
  - 补充断言覆盖 Nav2 成功但底盘反馈 L/R=0/0、下次执行模式切到 `ros` 的普通界面下一步和行程状态。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "Nav2 success.*wheel|IMU motion|explicit unproven|nonzero base commands"`
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
- 已通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`、`282 passed (282)`。
- 已通过：`git diff --check`
- 已确认：PC Node 仍监听 `*:7001`。
- live 只读摘要：Nav2 当前仍是 `goal_succeeded_wheel_feedback_not_proven`，`goal_execution_result_status=succeeded`，`base_command_mode=pwm`，`next_execution_base_command_mode=ros`，`base_command_nonzero_count=49`，`feedback_sample_count=239`，`wheel_lr_nonzero=false`，`L/R=0/0`；camera 当前仍是 `source_first_frame_failed / capture_read_returned_false`。

## 剩余风险

- 本轮没有触发真实小车运动，只修复 PC 普通界面对已有 Nav2/底盘反馈证据的解释和下一步引导。
- 现场 live 仍需继续复验摄像头首帧、Nav2 执行窗口 wheel raw L/R 非零和自由移动真实发布链路。
