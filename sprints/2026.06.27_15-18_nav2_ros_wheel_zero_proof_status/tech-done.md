# 2026-06-27 15:18 Nav2 ROS wheel zero proof status

## sprint_type: micro

## 设计结论

本轮只修自动驾驶排障证据口径，不触发真实 Nav2 执行。现场最新只读状态显示上位机服务已经配置
`base_command_mode=ros` 与 `nav2_base_command_mode=ros`，但最近一次 O11 artifact 仍是旧
`base_command_mode=pwm` 执行：`goal_succeeded`、非零底盘命令已进入 bridge、IMU 姿态有变化，
同窗口 `T1001 L/R` 仍是 `0/0`。因此当前问题不是雷达阻塞，也不是 PC 端口问题，而是下一轮需要
在 ROS 控制模式下复验 wheel raw L/R。

## 实际改动

- `onboard/scripts/o11_nav2_goal_execution_proof.py`
  - 新增 `wheel_zero_proof_status_for_mode()`，把“Nav2 成功 + 非零底盘命令 + wheel raw L/R 仍为 0”
    按真实 `base_command_mode` 输出成 `nav2_goal_succeeded_with_<mode>_commands_but_wheel_lr_zero`。
  - O11 finally 收口时不再写死 `nav2_goal_succeeded_with_pwm_commands_but_wheel_lr_zero`。
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`
  - 新增回归测试，锁定 `ros/pwm/非法值` 三种输入的 proof status。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 ROS 重跑后的缺口命名规则和安全边界。

## 验证结果

- 已通过：`python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof`
  - `Ran 7 tests in 0.002s`
  - `OK`
- 已通过：`python3 -m unittest onboard.tests.test_upper_robot_api -k nav2_goal_execute`
  - `Ran 3 tests in 0.009s`
  - `OK`
- 已通过：`python3 -m py_compile onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/upper_robot_api.py`
- 已部署到上位机 `/root/rober`：
  - 已通过：`python3 -m py_compile onboard/scripts/o11_nav2_goal_execution_proof.py`
  - 已通过：`python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof`
    - `Ran 7 tests in 0.008s`
    - `OK`
- 已通过：`git diff --check`

## 上位机只读证据

- SSH `root@192.168.1.11 -p 37878` 可达。
- `/api/base/status` 显示 `control_policy.base_command_mode=ros`、`control_policy.nav2_base_command_mode=ros`。
- `/api/base/status` 当前只读 `T=130` 回读可见 `T=1001`，但最新现场 L/R 为 `0/0`。
- `/api/nav2/goal/execution/latest` 是旧 `base_command_mode=pwm` artifact，非零命令和 IMU 运动迹象存在，
  wheel raw L/R 非零仍未证明。
- PC Node 仍监听 `*:7001`，`/api/robot-control/summary` 只读显示：
  `goal_execution_base_command_mode=pwm`、`next_execution_base_command_mode=ros`、
  `goal_execution_mode_rerun_status=pending_ros_rerun_after_pwm`、`wheel_lr=false`。
- 上位机脚本已包含 `wheel_zero_proof_status_for_mode()`；当前 latest 是历史 artifact，尚未触发新 proof status。

## 剩余风险

- 本轮没有发起新的 Nav2 goal、manual、free-roam start 或 `/cmd_vel`，所以没有证明真实 ROS 重跑后 L/R 非零。
- 摄像头仍是 UVC 首帧读取失败，不是本轮修复范围。
- 自动驾驶完整闭环还需要现场 operator 安全确认后执行一次 ROS 模式图上路线，并检查新 artifact 是否出现
  `nav2_goal_succeeded_with_nonzero_base_feedback`。
