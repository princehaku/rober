# 2026.06.25 19:30 PC trip summary route ready

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `行程操作` 现在会直接消费 summary 中已有的 `path_generated/path_generation_succeeded` 和路线点数；上位机已经生成 no-motion 路线时，卡片显示 `已准备` 与路线点数，不要求 operator 先重复点击 `准备行程（不发车）`。
- `pc-tools/workstation/test/App.test.ts`：补充 summary 路线点数回归，确认已有路线时可直接展示已准备，安全确认前按钮仍禁用，勾选后才显示 `检查行程` / `执行行程`，且不会自动调用 nav2 refresh、execute 或 base manual。
- `docs/product/pc_tools_workstation.md`：同步 summary 路线已准备的普通用户语义和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts -t "trip"`：通过，`8 passed / 64 skipped`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，`2 passed` test files，`163 passed` tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`path_generated=true`、`path_generation_succeeded=true`、`path_point_count=36`、`path_preview_point_count=36`、`robot_pose=null`、`lidar_lifecycle_running=false`。

## 剩余风险

- 本轮只改善 PC 首屏对已有路线的展示，不触发真实 NavigateToPose、不执行 `/api/base/manual`、不确认 delivery success；完整 Nav2 路线执行仍需 operator 显式点击 `执行行程` 并通过后端 gate。
