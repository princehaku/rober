# PC Nav2 Motion Material Diagnosis Micro Sprint

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `nav2_goal_next_action` 在最近 O11 执行已有非零底盘命令、`sends_base_motion_commands=true` 或 IMU 姿态变化时，不再把当前 `controller_server_active=false` 当成自动驾驶主因。
  - wheel raw L/R 仍然是完整路线验收硬门槛；新文案明确“主因不是雷达、相机或 controller”，剩余卡点是同窗口 `T=1001 L/R` 非零复验。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 PWM 非零命令但 wheel L/R=0 的 summary 回归。
  - 增加 IMU-only 运动材料时的下一步文案断言。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 O11 执行后 controller inactive 只是事后状态，不能覆盖已发底盘命令和 IMU 运动材料。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts --testNamePattern "Nav2.*wheel|IMU motion|motion material"`
  - `Test Files 1 passed (1)`
  - `Tests 4 passed | 128 skipped (132)`
- 已通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 310 passed (310)`
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - Vite 保留既有 chunk size warning，构建成功。
- 已通过：`git diff --check`
- 已通过：重启 PC Node 到 `0.0.0.0:7001` 后只读 live summary 复查
  - `status=goal_succeeded_wheel_feedback_not_proven`
  - `goal_execution_status=goal_succeeded`
  - `base_command_mode=pwm`
  - `goal_execution_base_command_nonzero_count=49`
  - `goal_execution_base_feedback_imu_attitude_delta_observed=true`
  - `wheel raw L/R=0/0`
  - `controller_server_active=false`
  - `nav2_goal_next_action=上次路线 action 成功但 wheel raw L/R=0/0 未非零；已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或 controller；勾选行程前安全确认后用 ROS 重跑图上路线`

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard、free-roam start、delivery、stop 或 `/cmd_vel`。
- 真实完整路线仍未完成：当前 live 证据是 action succeeded、底盘命令已发、IMU 有变化，但同窗口 `T=1001 L/R` 仍为 `0/0`。
- 摄像头仍是 UVC 无首帧且非页面独占；本轮不处理相机硬件输入/供电问题。
