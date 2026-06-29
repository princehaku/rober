# PC Nav2 当前服务状态所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增单端点 `readbackText` helper。
  - `readback_summary.nav2.planner_server_active/controller_server_active/controller_server_requested` 改为优先读取当前 `/api/nav2/status`，再读取 `/api/nav2/proof/latest`。
  - 最近一次 `/api/nav2/goal/execution/latest` 的 managed runtime 不再覆盖当前服务 active/requested 状态，只保留在 `goal_execution_*` 历史执行字段里。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新对应合同测试，验证当前 controller/requested=false 不会被 O11 历史 managed runtime 改写成 true。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 summary 与直连 Nav2 status 的当前状态优先规则。

## 验证结果

- `npm test -- catalog.test.ts`：通过，`166 passed`。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `npm run build`：通过。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`。
- live `curl http://127.0.0.1:7001/api/robot-control/summary`：
  - `readback_summary.nav2.nav2_stack_running=false`
  - `readback_summary.nav2.controller_server_active=false`
  - `readback_summary.nav2.controller_server_requested=false`
  - `readback_summary.nav2.path_generated=true`
  - `readback_summary.nav2.path_point_count=18`
- live `curl http://127.0.0.1:7001/api/robot-control/nav2/status`：
  - `proxy_status=status_loaded`
  - `lifecycle_running=false`
  - `controller_server_active=false`
  - `path_generated=true`
  - `path_point_count=18`

## 剩余风险

- 本轮只修正 PC summary 只读聚合优先级，未启动 Nav2 lifecycle，也未执行真实路线。
- 当前 live 自动驾驶仍需要现场安全确认后执行或恢复 runtime，再读取同窗口 wheel raw L/R。
