# 2026.06.30 10:15 PC Nav2 托管 Runtime 证据

sprint_type: micro

## 设计先行

本轮只修正 PC 首屏“图上路线”动作卡的只读证据，不执行 NavigateToPose、不发送任何运动命令。目标是把“自动驾驶为什么没法动”的排查焦点从文案猜测改成结构化事实：执行入口默认托管 Nav2 runtime、下次用 ROS 模式重跑、剩余验收缺口是同窗口 wheel raw L/R 非零。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `nav2_route.evidence`，增加 `managed_runtime_requested/started/lifecycle_ready_ok/cleanup_ok`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `nav2_route.evidence.managed_runtime_autostart` 改为从 Nav2 execution readback 和 route readiness 推导，不再用中文 next action 正则猜测。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 旧 summary fallback 同步改为结构化推导，并暴露 `data-managed-runtime-*` DOM 属性。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 PWM 成功但 wheel raw L/R=0/0、下次 ROS 重跑场景中的 managed runtime 动作卡证据。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通首屏 DOM 的 managed runtime 只读属性。
- `pc-tools/README.md`
  - 同步记录 Nav2 动作卡证据合同和不发车边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary tells the operator to rerun ROS Nav2 when PWM success lacks wheel raw L/R"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 167 skipped (168)`。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 217 skipped (218)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过；仅保留 Vite chunk size 提示。
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`，`Tests 386 passed (386)`。
- 通过：`git diff --check`。
- 通过：重启本机 PC Node 到 `0.0.0.0:7001`。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`。
  - `/tmp/rober_pc_workstation_7001.log` 显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读请求 `http://127.0.0.1:7001/api/robot-control/summary`。
  - `nav2_route.status=ready_needs_wheel_rerun`。
  - `nav2_route.evidence.managed_runtime_autostart=true`。
  - `managed_runtime_requested=true`、`managed_runtime_started=true`、`managed_runtime_lifecycle_ready_ok=true`、`managed_runtime_cleanup_ok=true`。
  - `last_base_command_mode=pwm`、`next_base_command_mode=ros`、`wheel_feedback_status=goal_succeeded_but_wheel_lr_zero`。
  - live 结论：当前不是雷达/相机/managed runtime 阻塞自动驾驶；下次应在现场安全确认后通过固定入口用 ROS 模式重跑，并在同窗口复验 wheel raw L/R 非零。

## 剩余风险

- 本轮只补只读合同和 DOM 证据，不执行 NavigateToPose、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 完整 Nav2 路线执行仍需要现场勾选安全确认后，用固定执行入口重跑 ROS 模式，并在同窗口确认 wheel raw L/R 非零。
