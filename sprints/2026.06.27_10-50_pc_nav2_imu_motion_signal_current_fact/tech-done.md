# PC Nav2 IMU 运动迹象首屏补强

sprint_type: micro

## 实际改动

- PC 普通用户首屏“当前事实”里的 Nav2 行程诊断新增 IMU 姿态变化信息：
  - 当 `goal_succeeded`、已发非零底盘命令、wheel raw L/R 仍为 `0/0`，但 `base_feedback_imu_attitude_delta_observed=true` 时，首屏会显示“车身姿态有变化，pitch/roll 变化”。
  - 仍保留“不是雷达或相机阻塞；卡在执行窗口 wheel raw L/R 非零复验”的结论，不把 IMU-only 当作完整路线通过。
- 更新 App 测试，覆盖当前真机形态：PWM 非零命令 49 条、底盘反馈 239 次、L/R=0/0、IMU pitch 变化。

## 验证结果

- 已读取真机 latest artifact：`nav2_goal_execution_latest.json` 中 `base_command_mode=pwm`、`nonzero_command_count=49`、`sample_count=239`、`wheel_feedback_lr_nonzero_proven=false`、`imu_attitude_delta_observed=true`、`max_abs_pitch_delta=24.210531`。
- 已通过定向测试：`npm test -- App.test.ts --testNamePattern "IMU-only|chassis feedback|current facts|Nav2 success"`，结果 `7 passed | 155 skipped`。
- 已通过前端 lint：`npm run lint`。
- 已通过前端生产构建：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 已通过全量前端测试：`npm test`，结果 `2 passed` test files，`283 passed` tests。

## 剩余风险

- 本轮只把现有运动迹象做成首屏所见即所得诊断，不执行新的 Nav2 或底盘运动。
- 当前完整 Nav2 路线执行仍未闭环：需要下一次在现场安全确认后按 `next_execution_base_command_mode=ros` 重新执行，并证明同一执行窗口 wheel raw L/R 非零。
