# 2026.06.29 14:35 upper_nav2_latest_readback_payload

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 修复 `enrich_nav2_goal_execution_latest_payload()` 在 latest artifact 已存在时补完字段后没有返回 payload 的问题。
  - 上位机只读 `/api/nav2/goal/execution/latest` 顶层新增/补齐 `status`、`result_status`、`base_command_mode`、`next_base_command_mode`、`wheel_feedback_lr_nonzero_proven`、`nav2_goal_execution_not_proven` 和 readback 运动字段。
  - 顶层继续保持 `robot_control_executed=false`、`sends_motion_commands=false`、`publishes_cmd_vel=false`、`safe_to_control=false`；真实执行事实只放在 `readback_*` 和 `latest_result`，避免只读 latest 被误当成发车。
- `onboard/tests/test_upper_robot_api.py`
  - 补充旧 PWM artifact 和 ROS retry artifact 的回归测试：上次 PWM 轮速未闭合时建议下一次 `ros`，上次 ROS 轮速未闭合时建议下一次 `speed`。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
  - 同步记录上位机 latest readback 修复和只读安全边界；轮速/反馈底层事实采用 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON/T1001 资料。

## 验证结果

- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py`
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_goal_execution_latest_derives_wheel_lr_gap_from_old_artifact onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_goal_execution_latest_returns_enriched_payload_for_speed_retry`
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api`，结果 `Ran 85 tests in 0.208s OK`。
- 通过：部署到上位机 `root@192.168.1.11:37878` 后远端 `python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py`，并按原参数重启 `0.0.0.0:8787`，新 PID `359774`。
- 通过：只读 live `GET http://192.168.1.11:8787/api/nav2/goal/execution/latest` 返回 `artifact=loaded`、`status=goal_succeeded`、`result_status=succeeded`、`base_command_mode=pwm`、`next_base_command_mode=ros`、`nav2_goal_execution_proven=false`、`wheel_feedback_lr_nonzero_proven=false`、`not_proven=[wheel_feedback_lr_nonzero, delivery_success, operator_dropoff_confirmation]`，同时顶层 `robot_control_executed=false`、`sends_motion_commands=false`、`publishes_cmd_vel=false`。
- 通过：只读 live `GET http://127.0.0.1:7001/api/robot-control/summary` 已消费新 readback：`goal_execution_base_command_mode=pwm`、`next_execution_base_command_mode=ros`、`safe_command_boundary.nav2_goal_execution_mode_label=上次 pwm，下次 ros`、`goal_execution_base_feedback_lr_nonzero_proven=false`、`goal_execution_base_command_nonzero_count=49`、`goal_execution_base_feedback_imu_attitude_delta_observed=true`。
- 通过：`git diff --check onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py pc-tools/README.md docs/product/pc_tools_workstation.md sprints/2026.06.29_14-35_upper_nav2_latest_readback_payload/tech-done.md`。

## 剩余风险

- 本轮只修复只读 latest 证据链，没有执行真实 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 完整自动驾驶仍需要现场勾选安全确认后重跑图上路线，并在同一执行窗口确认 WAVE ROVER 轮速 L/R 非零。
- 摄像头 live 仍是 UVC 无首帧，不是页面独占；雷达 live 仍需启动并刷新扫描后才能贴到当前地图。
