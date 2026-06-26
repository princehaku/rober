# PC Nav2 Execution Status WYSIWYG

## sprint_type

micro

## 实际改动

- 修改 `pc-tools/workstation/src/server/robotControlSummary.ts`：当最近 `/api/nav2/goal/execution/latest` 已证明完整路线执行成功时，`readback_summary.nav2.status` 优先显示 `goal_succeeded`，不再沿用规划 proof 的 `not_proven`。
- 修改 `pc-tools/workstation/test/catalog.test.ts`：扩展 live execution facts 测试，覆盖 `goal_execution_proven=true` 时顶层 Nav2 summary 状态也必须为 `goal_succeeded`。
- 更新 `docs/product/pc_tools_workstation.md`：记录 PC summary 的 Nav2 WYSIWYG 口径，明确该变更只修正状态解释，不新增 Nav2 execute、manual、keyboard、delivery、stop 或 `/cmd_vel` 调用。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "Nav2 execution proof"`，`1 passed / 106 skipped`。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build OK；保留既有 chunk size warning。
- 通过：`git diff --check`。
- 重启 PC Node 到当前源码后，`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，`readback_summary.nav2.status=goal_succeeded`、`goal_execution_proven=true`、`goal_execution_robot_control_executed=true`、`goal_execution_feedback_sample_count=8`。
- 当前 live 变更前证据：PC 7001 summary 已读到 `goal_execution_status=goal_succeeded`、`goal_execution_proven=true`、`goal_execution_robot_control_executed=true`、`goal_execution_feedback_sample_count=8`，但顶层 `readback_summary.nav2.status=not_proven`；本轮修复该同屏矛盾。

## 剩余风险

- 本轮只修正 PC summary 的 Nav2 执行结果所见即所得，不重新执行 Nav2，不证明新的真车运动。
- 真实底盘 wheel raw L/R 当前仍读到 `0/0`，完整“车确实动过”的轮速闭环还需要后续现场低速 HIL。
