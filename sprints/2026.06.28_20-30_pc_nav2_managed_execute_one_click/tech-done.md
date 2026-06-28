# 2026-06-28 20:30 PC Nav2 managed execute one click

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/server/robotControlSummary.ts`：`nav2_lifecycle_not_running` 继续保留为只读诊断 blocker，但路线已生成时不再阻塞 `safe_command_boundary.nav2_goal_ready`，普通首屏下一步说明执行时会自动启动自动驾驶 runtime。
- 修改 `pc-tools/workstation/src/server/index.ts`：`POST /api/robot-control/nav2/goal/execute` 显式转发 `managed_runtime_opt_in=true`、`managed_startup_s`、`managed_ready_timeout_s` 给上车 `/api/nav2/goal/execute`，让一次点击走 managed runtime + NavigateToPose。
- 修改 `pc-tools/workstation/src/shared/contracts.ts`：补齐 Nav2 execute 请求和回包里的 managed runtime 字段。
- 修改 `pc-tools/workstation/test/catalog.test.ts`：把 lifecycle stopped 场景改为“保留诊断但不挡执行”，并断言 execute 请求体包含 `managed_runtime_opt_in=true`。
- 更新 `docs/product/pc_tools_workstation.md`：记录一键托管执行口径和安全边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "managed runtime can start lifecycle|Nav2 goal execution reuses minimal PC preflight|defaults Nav2 goal execution"`，结果 `3 tests passed`。
- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "Nav2 route|nav2 goal|automatic"`，结果 `4 tests passed`。
- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts`，结果 `153 tests passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 成功；仍有既有 chunk size warning。
- 通过：`git diff --check pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/server/robotControlSummary.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md sprints/2026.06.28_20-30_pc_nav2_managed_execute_one_click/tech-done.md`
- 通过：重启 PC 7001 后只读复核 `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`，结果 `nav2_goal_ready=true`、`nav2_goal_blockers=[]`、`current_blockers=nav2_lifecycle_not_running`、`nav2_goal_next_action` 包含“执行时会自动启动自动驾驶 runtime”、`keyboard_control_start_ready=true`、`free_roam_start_ready=true`。

## 剩余风险

- 本轮不实际点击执行路线，不发送 NavigateToPose 或 `/cmd_vel`；真实 wheel raw L/R 非零、完整路线执行和 delivery success 仍需要现场安全确认后实测。
- 如果上车 managed runtime 启动失败，执行回包仍会 fail-closed，需要看 `/api/nav2/goal/execution/latest` 的 helper stderr/root cause。
