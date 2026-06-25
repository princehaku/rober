# 2026.06.25 18:40 PC route path caption

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏地图 caption 新增路线状态，已把 no-motion planner `path_preview_points` 叠到真实地图上时显示 `路线已显示 N/M 个点`；路线已生成但地图画面未加载时提示刷新地图画面；未生成时不额外显示路线文案，保持默认首屏简洁。
- `pc-tools/workstation/test/App.test.ts`：扩展路线 overlay 回归测试，锁定地图 caption 的路线点数显示，并继续断言不触发 Nav2 execute、delivery complete 或 manual。
- `docs/product/pc_tools_workstation.md`、`docs/navigation/fixed_route_workflow.md`：同步普通地图路线 WYSIWYG 口径和不发车边界。

## 验证结果

- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "draws the latest Nav2 goal"`：通过，`1 passed / 69 skipped`。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "renders Robot Control V1 by default"`：通过，确认无路线时普通首屏不额外出现“路线”文案。
- `cd pc-tools/workstation && npm test`：通过，`2 passed` test files，`161 passed` tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`path_generated=true`、`path_generation_succeeded=true`、`path_point_count=36`、`path_preview_point_count=36`、`path_preview_source_point_count=36`、`path_preview_frame_id=map`。

## 剩余风险

- 本轮只把已生成的 no-motion planner 路线更明确地显示在普通地图 caption 上，不执行 NavigateToPose，不证明真实路线执行、delivery success 或底盘运动。
