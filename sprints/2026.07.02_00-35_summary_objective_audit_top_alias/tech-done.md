# Summary 顶层当前卡点与目标总览 Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增当前卡点和四项目标总览 alias，全部与 `live_closure_summary` 同源：
  - `status`
  - `live_status`
  - `summary_plain`
  - `next_action_plain`
  - `objective_audit_status`
  - `objective_audit_total_count`
  - `objective_audit_done_count`
  - `objective_audit_remaining_count`
  - `objective_audit_next_objective_id`
  - `objective_audit_missing_objective_ids`
  - `objective_audit_summary_plain`
  - `objective_audit_items`
  - `fixed_objective_audit_summary_endpoint=/api/robot-control/summary`
  - `objective_audit_sends_motion_when_clicked=false`
- `console_status` 继续表达 summary API 自身是否 blocked；`status/live_status` 表达当前业务卡点。
- 同步更新 `RobotControlSummaryResponse` contract、`robotControlSummary.test.ts`、`catalog.test.ts` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts -t "map"`：通过，1 个 test file，5 passed，4 skipped。
- `npm test -- --run test/catalog.test.ts -t "live-summary"`：通过，1 个 test file，1 passed，180 skipped。
- `npm test`：通过，3 个 test files，421 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，当前监听 PID `33553`。
- 真实只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 顶层读回：
  - `console_status=loaded_fail_closed_summary`
  - `status=needs_wheel_rerun`
  - `live_status=needs_wheel_rerun`
  - `summary_plain=当前卡点：图上路线已经有执行成功读数，但同窗口轮速 L/R 还没有非零闭环。`
  - `next_action_plain=勾现场安全确认后重跑图上路线，并在同一个执行窗口复验轮速 L/R 非零。`
  - `objective_audit_status=in_progress`
  - `objective_audit_total_count=4`
  - `objective_audit_done_count=1`
  - `objective_audit_remaining_count=3`
  - `objective_audit_next_objective_id=motion`
  - `objective_audit_missing_objective_ids=["motion","wysiwyg","mapping"]`
  - `objective_audit_items_count=4`
  - `fixed_objective_audit_summary_endpoint=/api/robot-control/summary`
  - `objective_audit_sends_motion_when_clicked=false`

## 剩余风险

- 本轮只修 summary 顶层读数，不改变任何控制 gate。
- 当前四项目标仍未完成，真实运动闭环、相机首帧和雷达贴图仍需现场材料或显式安全确认后验证。
- 本轮不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop，也不发布 `/cmd_vel`。
