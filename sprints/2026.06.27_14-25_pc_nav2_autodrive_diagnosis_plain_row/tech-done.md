# PC Nav2 自动驾驶诊断行

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 的普通首屏事实条新增“自动驾驶”诊断行。
- 当最近 Nav2 `goal_succeeded` 但执行窗口 `wheel raw L/R` 未非零时，直接说明不是摄像头或雷达阻塞，而是上次底盘命令已发出但 wheel raw 闭环未完成，并提示用 ROS 重跑图上路线。
- 更新 `docs/product/pc_tools_workstation.md`，记录该诊断只消费只读 summary/latest，不自动执行 Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "keeps IMU-only route arrival visible while calling out zero wheel readback"`，结果 `1 passed | 164 skipped`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `291 passed`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 构建成功，仍有既有 `Some chunks are larger than 500 kB` 警告。
- 通过：只读 live 摘要 `GET http://127.0.0.1:7001/api/robot-control/summary?robot_base_url=http://192.168.1.11:8787` 显示 `nav2_status=goal_succeeded_wheel_feedback_not_proven`、`last_mode=pwm`、`next_mode=ros`、`wheel_status=goal_succeeded_but_wheel_lr_zero`、`base_lr=0/0`。
- 通过：构建产物 `pc-tools/workstation/dist/assets/index-DptZl5MS.js` 包含新增“自动驾驶：不是摄像头或雷达阻塞”诊断文案。

## 剩余风险

- 本轮未在未确认现场安全的情况下触发真实 Nav2 发车；live 仍需要 operator 勾选行程前安全确认后，才能用 ROS/T=13 重跑图上路线并观察同窗口 wheel raw L/R。
