# 上车 Nav2 默认执行跟随下一次模式

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `nav2_goal_execute_base_command_mode_from_latest()`。
  - `/api/nav2/goal/execute` 在请求体没有显式 `base_command_mode/nav2_base_command_mode` 时，先只读 latest 的 `next_base_command_mode`；合法时作为本轮 helper 的 `base_command_mode`。
  - 显式传入合法模式仍优先；显式非法模式仍回落配置默认，不从旧 latest 偷偷切换。
- `onboard/tests/test_upper_robot_api.py`
  - 新增 ROS/T=13 零轮速 latest 后默认切到 `speed` 的单元测试。
  - 保留显式 `pwm` override 测试，防止诊断模式被默认逻辑覆盖。
- `docs/process/okr_progress_log.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录上车端默认模式选择修复与现场验证边界。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_goal_execute_defaults_to_speed_after_ros_wheel_zero_latest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_goal_execute_lifts_base_motion_flags_from_latest_result onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_goal_execute_allows_explicit_base_command_mode_override`，3 tests OK。
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api`，89 tests OK / 1 skipped。
- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py`。
- 通过：`git diff --check`。
- 通过：同步 `upper_robot_api.py` 到真实上位机 `/root/rober/onboard/scripts/upper_robot_api.py`，重启 8787 后 `lsof` 显示单个 `python3 *:8787 (LISTEN)`。
- 通过：真实上位机纯函数验证 ROS 零轮速 latest：
  - `next_base_command_mode=speed`
  - `nav2_goal_execute_base_command_mode_from_latest("ros", latest)=speed`
- 通过：PC 7001 只读 summary 仍显示当前真实 latest 为旧 PWM 后等待 ROS 复验，`nav2_goal_ready=true`、`current_blocker_reasons=none`；本轮没有触发真实 goal。

## 剩余风险

- 本轮修复的是默认模式选择，不发送 Nav2 goal、不证明 wheel L/R 非零。
- 真实完整路线闭环仍需要现场安全确认后执行；如果下一轮 ROS/T=13 仍 wheel L/R=0/0，后续未显式指定模式的执行会自动切 SPEED/T=1。
- 当前摄像头仍是 UVC 源头无帧；该缺口不阻止低速自由移动或 Nav2 路线重跑，但会阻止建图启动验收。
