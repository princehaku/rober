# Tech Done

sprint_type: micro

## 实际改动

- 补齐 `GET /api/robot-control/nav2/goal/execution/latest` 的直连只读边界字段：`readback_only=true`、`nav2_goal_execution_latest_readback_only=true`、`sends_motion_when_clicked=false`、`starts_* = false`、`submits_delivery=false`、`stops_motion=false` 和 `robot_control_executed=false`。
- 补齐 `GET/POST /api/robot-control/base/feedback-samples` 统一响应里的轮速读回边界字段：`readback_only=true`、`base_feedback_samples_readback_only=true`、同组 no-motion flags，以及面向现场脚本的 `next_action_plain`。
- 更新 PC workstation 共享契约、回归测试和产品文档，明确 Nav2 latest 与 wheel feedback samples 都只是读回，不会发车、不启动 Nav2/manual/keyboard/free-roam/建图/雷达 lifecycle，不提交 delivery、不 stop、不发布 `/cmd_vel`。

## 验证结果

- `npm test -- test/catalog.test.ts`：通过，`183 passed`。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过，无空白错误。
- 已重启本机服务到 `0.0.0.0:7001`，进程 PID `55607`。
- Live 只读复验：
  - `GET http://127.0.0.1:7001/api/robot-control/nav2/goal/execution/latest` 返回 `proxy_status=latest_loaded`、`readback_only=true`、`nav2_goal_execution_latest_readback_only=true`、`sends_motion_when_clicked=false`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`submits_delivery=false`、`stops_motion=false`、`robot_control_executed=false`。
  - `GET http://127.0.0.1:7001/api/robot-control/base/feedback-samples` 返回 `proxy_status=samples_forwarded`、`readback_only=true`、`base_feedback_samples_readback_only=true`、同组动作边界均为 `false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只做 no-motion 读回合同修复，未在现场勾安全确认执行 Nav2、键盘或自由移动，所以 `same_window_wheel_lr_nonzero`、`delivery_success` 仍需要真实安全确认后的 HIL 复验。
- 相机首帧仍受当前 USB 12M full-speed / first frame timeout 影响；该问题会阻塞建图验收，但不作为本轮读回合同的完成条件。
