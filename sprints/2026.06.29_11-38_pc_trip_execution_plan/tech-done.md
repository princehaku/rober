# PC 行程执行包

sprint_type: micro

## 实际改动

- 普通首屏“行程操作”新增“行程执行包”三行只读提示：执行模式、自动驾驶 runtime、轮速验收。
- 执行模式行直接展示本次执行请求使用的底盘命令模式；旧 PWM 记录需要复验时会写明“上次 PWM，本次请求 ROS”。
- runtime 行说明自动驾驶服务停着时由执行接口托管启动，不把 runtime 停止误当成额外预检。
- 轮速验收行强调完整行程必须在本次执行窗口读到轮速 L/R 非零，IMU 只作运动迹象。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`，1 passed。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "keeps the summary-requested ROS rerun visible for an old PWM route with zero wheel readback"`，1 passed。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "lets a ready route execute through managed Nav2 runtime when lifecycle is stopped"`，1 passed。
- 通过：`npm --prefix pc-tools/workstation test`，2 files / 376 tests passed。
- 通过：`npm --prefix pc-tools/workstation run build`。
- 通过：PC API 已重启到 `0.0.0.0:7001`，PID `84548`。
- 通过：只读 `GET /api/robot-control/summary` 返回 `ready_action_items=["nav2_route_execution","keyboard_continuous_control","free_move"]`，
  `blocked_action_items=["camera_wysiwyg","radar_map_points_wysiwyg","mapping_start"]`。
- 通过：live Nav2 只读状态为 `nav2_goal_ready=true`、`nav2_goal_execution_mode_label="上次 pwm，下次 ros"`、
  `next_execution_base_command_mode="ros"`、`nav2_stack_running="false"`，并明确执行会自动启动自动驾驶 runtime。

## 剩余风险

- 本轮只让 PC 端把行程执行合同展示得更直接，不触发真实 Nav2 执行；完整路线执行和同窗口轮速 L/R 非零仍需要现场勾安全确认后复验。
- live 只读状态仍显示 `goal_execution_base_feedback_latest_raw_left/right=0/0` 且 `goal_execution_base_feedback_lr_nonzero_proven=false`，所以完整行程尚未硬件闭环完成。
- 摄像头首帧和雷达新鲜扫描仍是建图条件，不影响行程、键盘或自由移动的最小发车确认。
