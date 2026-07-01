# Summary runbook gap alias micro sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`GET /api/robot-control/summary` 顶层补齐四项 runbook 缺口 alias，覆盖当前主推荐、完整行程、键盘连续手控、自由移动和建图的 ready/completed/proof_status/missing_evidence/proof_plain。
- `pc-tools/workstation/src/shared/contracts.ts`：同步新增这些只读字段类型。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：断言顶层 alias 与 `live_motion_runbook_items` 同源，且完整行程、键盘、自由移动、建图缺口直读可见。
- `docs/product/pc_tools_workstation.md`：记录顶层 runbook 缺口 alias 合同。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，`9 passed`。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "live-summary"`，`1 passed | 180 skipped`。
- 已通过：`git diff --check`。
- 已通过：`cd pc-tools/workstation && npm test`，`421 passed`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。
- 已通过：重启 `0.0.0.0:7001`，当前监听 PID `20368`。
- 已通过：只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `primary_missing_evidence=[same_window_wheel_lr_nonzero,delivery_success]`、`trip_missing_evidence=[same_window_wheel_lr_nonzero,delivery_success]`、`keyboard_missing_evidence=[same_hold_window_wheel_lr_nonzero,stop_after_release]`、`free_move_missing_evidence=[free_roam_latest_motion_ready]`、`mapping_missing_evidence=[camera_first_frame]`，并返回各项 `proof_plain`。

## 剩余风险

- 本轮只解释当前验收缺口，不执行 Nav2/manual/keyboard/free-roam/建图/delivery/stop，也不发布 `/cmd_vel`。
- 真实完成仍需要现场安全确认后执行/验证：完整行程同窗口 wheel L/R 与 delivery success、键盘按住窗口 wheel L/R 和松开 stop、自由移动 latest 运行读数、建图传感器 ready。
