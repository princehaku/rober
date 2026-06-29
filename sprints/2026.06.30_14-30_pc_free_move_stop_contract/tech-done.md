# 2026.06.30 14:30 PC 自由移动停止兜底合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `free_move` action card evidence 新增固定自由移动 stop 端点、停止请求 pending、start 清除停止请求和停止请求不阻塞启动字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 后端 summary 为自由移动卡固定返回 `/api/robot-control/free-roam/autonomy/stop`。
  - 从 `readback_summary.free_roam.stop_required` / `decision_state` 派生当前是否有停止请求，并在 start ready 时声明 start 会先清除停止请求。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 前端兼容旧 summary，自动派生同一份自由移动停止兜底合同。
  - 普通首屏 action card DOM 暴露 `data-fixed-free-roam-stop-endpoint`、`data-free-roam-stop-request-pending`、`data-start-will-clear-stop-request` 和 `data-motion-start-blocked-by-stop-request`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 补后端 action card 和前端 DOM 断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录自由移动停止兜底、停止请求处理和安全边界。

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
  - `free_move.evidence.fixed_free_roam_stop_endpoint=/api/robot-control/free-roam/autonomy/stop`。
  - `free_move.evidence.free_roam_stop_request_pending=true`。
  - `free_move.evidence.start_will_clear_stop_request=true`。
  - `free_move.evidence.motion_start_blocked_by_stop_request=false`。
  - `robot_control_executed=false`。

## 剩余风险

- 本轮只补只读合同和 DOM evidence，不自动启动自由移动、不发送 stop/manual/keyboard/Nav2/delivery 或 `/cmd_vel`。
- live 当前自由移动仍需要现场勾选安全确认后执行，并用真实运动窗口确认车体运动。
