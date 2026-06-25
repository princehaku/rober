# 2026.06.25 19:40 PC trip progress route ready

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 的 `行程执行` 行、`当前读数` 和验收卡点现在会消费 summary 路线准备状态，显示 `路线已准备 N 个点`，不再只说“还没读到行程成功结果”。
- `pc-tools/workstation/test/App.test.ts`：扩展 summary 路线准备回归，确认行程卡片和本轮进度都显示路线点数，且不会自动触发 nav2 refresh、execute 或 base manual。
- `docs/product/pc_tools_workstation.md`：同步本轮进度读取路线准备状态的用户语义和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts -t "trip"`：通过，`8 passed / 64 skipped`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，`2 passed` test files，`163 passed` tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`path_generated=true`、`path_generation_succeeded=true`、`path_point_count=36`、`path_preview_point_count=36`、`keyboard_mode=bounded_repeating_manual_pulse`。

## 剩余风险

- 本轮只改 PC 普通进度提示；完整 Nav2 路线执行仍未在本轮触发，必须由 operator 显式点击 `执行行程` 并通过后端 execute gate。
