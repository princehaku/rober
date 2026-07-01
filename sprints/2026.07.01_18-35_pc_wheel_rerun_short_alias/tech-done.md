# PC 完整 Nav2 轮速复验短 alias

sprint_type: micro

## 实际改动

- `live_closure_summary` 和 `/api/robot-control/live-summary` 新增完整 Nav2 轮速复验短 alias：可否勾安全确认重跑、固定执行 endpoint、执行会发车、安全确认要求、读回端点、四段验收 marker、当前缺口和无额外预检说明。
- 普通首屏 `plain-live-closure-summary` 和轮速复验说明卡同步暴露这些 `data-wheel-rerun-*` 字段，现场脚本不用再拼多个长字段判断当前路线复验合同。
- 更新测试和产品文档，明确完整行程复验仍只由用户勾现场安全确认后执行；本轮不自动执行 Nav2，不发送任何运动命令。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "minimal precheck fields for same-window wheel rerun"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "wheel rerun"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 构建成功；保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，418 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`；`HEAD http://127.0.0.1:7001/map` 返回 `200`，`GET /api/robot-control/live-summary` 返回 `status=needs_wheel_rerun`、`nav2_route_ready=true`、`nav2_goal_succeeded=true`、`wheel_lr_nonzero_proven=false`、`wheel_rerun_ready_for_safety_confirm=true`、`wheel_rerun_start_endpoint=/api/robot-control/nav2/goal/execute`、`wheel_rerun_start_sends_motion=true`、`wheel_rerun_requires_safety_confirm=true`、`wheel_rerun_required_success_markers=["map_route_visible","nav2_goal_succeeded","same_window_wheel_lr_nonzero","delivery_success"]`。

## 剩余风险

- 本轮只改善完整 Nav2 路线复验的可读合同；真实 `wheel_lr_nonzero_proven`、`keyboard_continuous_motion_verified` 和 `delivery_success` 仍需要现场安全确认后执行对应动作并读回同窗口 wheel L/R 非零。
