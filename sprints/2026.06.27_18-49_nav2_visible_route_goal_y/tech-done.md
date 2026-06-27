# 2026.06.27 18:49 Nav2 可见路线终点复验

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/test/App.test.ts`
  - 新增普通首屏路线执行回归：当当前地图路线终点是 `x=0.80, y=0.05` 时，点击 `执行图上路线` 必须把可见终点作为 Nav2 execute 请求体发送，且默认 `base_command_mode=ros`、`confirm_navigation_execution=true`。
  - 回归同时确认没有调用 `/api/base/manual` 或 `/cmd_vel`，避免把路线执行入口退回手控或裸运动通道。
- `docs/product/pc_tools_workstation.md`
  - 记录现场 no-motion preflight 结论：Nav2 行程预检只读取 localize proof、Nav2 proof 和 Nav2 status，不依赖摄像头首帧或雷达新鲜度，也不执行机器人控制。

## 验证结果

- 现场只读预检：
  - `POST http://127.0.0.1:7001/api/robot-control/nav2/goal/preflight?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - body: `{"goal_frame_id":"map","goal_x":0.8,"goal_y":0.05,"goal_yaw":0,"confirm_navigation_preflight":true}`
  - 结果：`proxy_status=preflight_passed`，`missing_requirements=[]`，`blocked_reasons=[]`，`remote_methods_used=["GET"]`，读取端点为 `/api/localize/proof/latest`、`/api/nav2/proof/latest`、`/api/nav2/status`，`robot_control_executed=false`。
- 现场 latest 只读：
  - `GET http://127.0.0.1:7001/api/robot-control/nav2/goal/execution/latest?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - 结果：旧记录为 `status=goal_succeeded`、`base_command_mode=pwm`、`base_feedback_lr_nonzero_proven=false`、`base_feedback_latest_left_speed=0`、`base_feedback_latest_right_speed=0`，因此自动驾驶缺口是旧 PWM action 成功但 wheel raw L/R 未闭合，需在现场安全确认后用 ROS 重跑。
- targeted Vitest:
  - `npm test -- --run test/App.test.ts -t "executes the visible route endpoint with nonzero Y"`
  - 结果：`1 passed | 174 skipped`。

## 剩余风险

- 本轮没有执行真实 Nav2 goal，因为会触发小车运动；仍需要现场 operator 明确安全确认后，点击普通首屏 `用 ROS 重跑图上路线/执行图上路线`，再检查同窗口 wheel raw L/R 是否非零。
- 摄像头现场当前为 `source_first_frame_failed` 且 `uvc_no_frame_not_exclusive`，结论不是页面独占，而是 `/dev/video1` 无首帧；需要继续查 USB、摄像头输入、供电或换 known-good UVC。
- 当前雷达 runtime `/scan` 新鲜但最近障碍约 `0.04m` 时，只能提示原地换向避让；低速自由移动启动不依赖雷达，但直行策略和建图验收仍受障碍距离影响。
