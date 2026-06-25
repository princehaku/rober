# 2026.06.25 19:50 PC trip progress safety hint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`本轮进度 / 行程执行` 在路线已准备但安全确认未勾选时，提示 `先勾选行程前确认`；勾选后才提示 `下一步检查或执行行程`。
- `pc-tools/workstation/test/App.test.ts`：扩展 summary 路线准备回归，覆盖安全确认前后的本轮进度文案分流。
- `docs/product/pc_tools_workstation.md`：同步行程进度安全确认提示的普通用户语义。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts -t "trip"`：通过，`8 passed / 64 skipped`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，`2 passed` test files，`163 passed` tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`path_generated=true`、`path_generation_succeeded=true`、`path_point_count=36`、`path_preview_point_count=36`、`keyboard_mode=bounded_repeating_manual_pulse`。

## 剩余风险

- 本轮只改普通首屏提示，不触发真实 NavigateToPose、manual、keyboard、delivery 或 `/cmd_vel`；完整 Nav2 路线执行仍需现场显式点击 `执行行程`。
