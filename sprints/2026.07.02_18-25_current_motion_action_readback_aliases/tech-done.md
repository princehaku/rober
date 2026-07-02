# Current Motion Action Readback Aliases

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 给 `current_motion_action_*` 补齐当前主运动动作的读回和验收字段：
    - `current_motion_action_readback_endpoints`
    - `current_motion_action_required_success_markers`
    - `current_motion_action_proof_status`
    - `current_motion_action_missing_evidence`
    - `current_motion_action_proof_plain`
  - 字段复用 `fieldAcceptanceNextStep` 和 primary safety action，不新增第二套排序逻辑。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-trip-current-motion-action`、`plain-trip-closure-gate`、`plain-trip-execute`、`plain-trip-execution-gauge` 继续消费 `current_motion_action_*`，并新增 readback/missing/proof DOM 证据。
  - 普通行程短行现在会直接显示当前还差 `same_window_wheel_lr_nonzero`、`delivery_success` 等缺口。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlSummaryResponse` 的 `current_motion_action_*` 可选字段。
- `pc-tools/workstation/test/App.test.ts`
  - 补普通 PC 行程区 DOM 断言，确认当前运动动作显示缺口但不暴露 `/api/` 到可见文案。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 补 summary 断言，确认 current motion action 的读回、缺口和 proof 字段可用。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补 catalog smoke，确认 current motion action 字段与 primary safety action / trip alias 同源。
- `docs/product/pc_tools_workstation.md`
  - 同步 `current_motion_action_*` 新增字段和 DOM 合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`
  - `Test Files 3 passed (3)`，`Tests 428 passed (428)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite build 成功，仅保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`git diff --check`
- 通过：PC `0.0.0.0:7001` live smoke
  - 服务 PID `54114`，`/` 和 `/map` 均返回 `200 text/html; charset=utf-8`。
  - `GET /api/robot-control/summary` 返回 `current_motion_action_id=run_nav2_route`、`current_motion_action_display_label=重跑图上行程并复验轮速`、`current_motion_action_start_endpoint=/api/robot-control/nav2/goal/execute`、`current_motion_action_readback_endpoints=[map preview, nav2 latest, base feedback samples, delivery latest, summary]`、`current_motion_action_missing_evidence=[same_window_wheel_lr_nonzero, delivery_success]`、`current_motion_action_minimal_precheck_safety_only=true`、`current_motion_action_camera_preflight_required=false`、`current_motion_action_radar_preflight_required=false`、`current_motion_action_sends_motion=true`。

## 剩余风险

- 本轮只补当前主运动动作的验收读回展示和脚本 alias，不实际发车；真实 Nav2 重跑、同窗口 wheel L/R 非零和 delivery success 仍需要现场勾安全确认后执行。
