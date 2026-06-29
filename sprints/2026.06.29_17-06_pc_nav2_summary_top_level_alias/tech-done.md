# PC Nav2 顶层摘要别名

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`GET /api/robot-control/summary` 现在返回顶层 `nav2_summary`，内容直接复用 `readback_summary.nav2`。正常态和 fail-closed 态都保持一致，避免外部脚本读顶层自动驾驶状态时拿到空。
- `pc-tools/workstation/src/shared/contracts.ts`：补充 `RobotControlSummaryResponse.nav2_summary` 类型。
- `pc-tools/workstation/test/catalog.test.ts`：补充正常 summary、缺地址和 unsafe URL 场景的 alias 一致性断言。
- `pc-tools/README.md`：同步记录 `nav2_summary` 只读别名边界。

## 验证结果

- `npm test -- --run test/catalog.test.ts`：`1 passed`，`166 passed`。
- `npm run build`：TypeScript、Vite build、server TypeScript 均通过。
- 本机部署：已重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 `node` 监听 `*:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- Live summary：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `nav2_summary` 顶层字段；`nav2_summary.status === readback_summary.nav2.status` 为 true，当前值 `goal_succeeded_wheel_feedback_not_proven`，`next_execution_base_command_mode=ros`，`current_blocker_reasons=nav2_lifecycle_not_running`，`safe_command_boundary.nav2_goal_ready=true`。

## 剩余风险

- 该改动只改善 PC/API 可读性，帮助现场直接看到“自动驾驶为什么不能动 / 下一步怎么重跑”；没有触发 Nav2 goal、键盘、自由移动、雷达启动或 `/cmd_vel`。
- 完整行程执行仍需要现场勾选安全确认后显式重跑，并用同窗口轮速 L/R 非零证明。
