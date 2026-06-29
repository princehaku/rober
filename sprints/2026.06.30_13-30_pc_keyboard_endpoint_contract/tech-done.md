# 2026.06.30 13:30 PC 键盘连续手控端点合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `keyboard_control` action card evidence 新增固定手控 pulse 和停止代理字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 后端 summary 为键盘卡固定返回 `/api/robot-control/base/manual` 和 `/api/robot-control/base/stop`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 前端兼容旧 summary，自动从 safe boundary 派生同一份端点合同。
  - 普通首屏 action card DOM 暴露 `data-fixed-keyboard-manual-endpoint` / `data-fixed-keyboard-stop-endpoint`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 补后端 action card 和前端 DOM 断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录键盘连续手控固定端点与安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 169 skipped (170)`。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite build 成功；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读检查 `GET /api/robot-control/summary`。
  - `keyboard_control.evidence.fixed_keyboard_manual_endpoint=/api/robot-control/base/manual`。
  - `keyboard_control.evidence.fixed_keyboard_stop_endpoint=/api/robot-control/base/stop`。
  - `hold_to_move_required=true`、`arm_sends_motion=false`、`requires_keydown_for_motion=true`。
  - `robot_control_executed=false`。

## 剩余风险

- 本轮只补只读合同和 DOM evidence，不自动启用键盘、不发送 manual/stop、不执行 Nav2/free-roam/delivery 或 `/cmd_vel`。
- 键盘连续手控真正闭环仍需要现场勾选安全确认后按住方向键/WASD，并在同窗口确认 wheel raw L/R 非零。
