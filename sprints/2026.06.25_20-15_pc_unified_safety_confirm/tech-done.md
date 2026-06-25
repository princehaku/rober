# 2026.06.25 20:15 PC unified safety confirm

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏新增统一安全确认状态，`移动/导航` 与 `扫地式建图` 两处复选框同步；行程执行、键盘连续手控、扫地式建图启动/保存都复用同一个最小安全确认。
- `pc-tools/workstation/test/App.test.ts`：新增统一安全确认回归，覆盖从移动/导航勾选后扫图无需二次确认、取消扫图确认会同步锁回行程/键盘/扫图，并确认不会自动调用任何控制接口。
- `docs/product/pc_tools_workstation.md`：同步 PC 普通首屏统一安全确认口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts -t "one plain safety confirmation"`：通过，`1 passed / 72 skipped`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，`2` 个 test files，`164 passed`。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 只读 summary smoke：`node` 正在监听 `TCP *:7001`；`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`、`connection=readable`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`path_generated=true`、`path_generation_succeeded=true`、`path_point_count=36`、`path_preview_point_count=36`、`keyboard_mode=bounded_repeating_manual_pulse`、`free_roam_autonomy=locked`。

## 剩余风险

- 本轮只统一普通首屏安全确认 gate，不触发真实 NavigateToPose、manual、keyboard、delivery、map start/save 或 `/cmd_vel`。
- 完整 Nav2 路线执行、delivery success、wheel raw L/R 非零和真实扫地式自由建图仍需现场显式操作和真实上位机证据。
