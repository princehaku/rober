# PC Nav2 直连状态最小发车确认文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 调整 `GET /api/robot-control/nav2/status` 的 `plain_hint/next_action_plain`。
  - 当图上路线已生成但当前 controller 或 lifecycle 未 active 时，直连状态不再提示普通用户“先手动恢复 runtime”，而是说明执行图上路线只需勾现场安全确认，执行接口会托管启动自动驾驶 runtime，并在同窗口复验轮速 L/R。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录直连 Nav2 status 与 summary 一致采用最小发车确认口径。

## 验证结果

- `npm run build`：通过。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`。
- live `curl http://127.0.0.1:7001/api/robot-control/nav2/status`：
  - `proxy_status=status_loaded`
  - `plain_hint=Nav2 状态已读到：path_ready_with_service_blockers；路线点 18；控制服务=false。`
  - `next_action_plain=图上路线已生成；当前控制服务或 lifecycle 未 active。执行图上路线只需勾现场安全确认，执行接口会托管启动自动驾驶 runtime，并在同窗口复验轮速 L/R。`
  - `lifecycle_running=false`
  - `controller_server_active=false`
  - `path_generated=true`
  - `path_point_count=18`
  - `sends_motion_commands=false`

## 剩余风险

- 本轮只修正 PC 只读诊断文案，不启动 Nav2 lifecycle，不执行真实路线。
- 真实完整 Nav2 路线执行仍需要现场安全确认后重跑并读取同窗口 wheel raw L/R。
