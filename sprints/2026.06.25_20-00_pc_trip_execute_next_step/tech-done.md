# 2026.06.25 20:00 PC trip execute next step

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当 summary 或 no-motion proof 已经读到正数路线点、并且普通用户已勾选行程前安全确认时，`行程操作` 和 `本轮进度 / 行程执行` 直接提示 `可执行行程 / 下一步：执行行程`；路线未准备时仍保留检查/准备口径。
- `pc-tools/workstation/test/App.test.ts`：更新 summary 路线已准备回归，覆盖安全确认前后文案、验收卡点和“不自动调用 Nav2 execute/manual/cmd_vel”的边界。
- `docs/product/pc_tools_workstation.md`：同步 PC 普通首屏路线已准备后的下一步语义，明确焦点/文案收敛不等于自动发车。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts -t "prepared trip state"`：通过，`1 passed / 71 skipped`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，`2` 个 test files，`163 passed`。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 只读 summary smoke：`node` 正在监听 `TCP *:7001`；`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`path_generated=true`、`path_generation_succeeded=true`、`path_point_count=36`、`path_preview_point_count=36`、`keyboard_mode=bounded_repeating_manual_pulse`。

## 剩余风险

- 本轮只改普通首屏从“路线已准备”到“执行行程”的下一步提示，不触发真实 NavigateToPose、manual、keyboard、delivery 或 `/cmd_vel`。
- 完整 Nav2 路线执行、delivery success、wheel raw L/R 非零和 PC 键盘连续手控仍需现场显式操作和真实上位机证据。
