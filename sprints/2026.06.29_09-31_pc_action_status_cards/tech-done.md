# PC 普通首屏动作状态卡

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增只读 `RobotControlActionStatusCard` 合同，允许 summary 顶层返回 `action_status_cards[]`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从同轮 `readback_summary` 与 `safe_command_boundary` 派生 7 张动作状态卡：画面、地图、地图雷达点、图上路线、键盘手控、自由移动和建图启动。卡片明确下一步、是否需要安全确认、是否会触发运动、是否影响建图，以及是否不阻塞自由移动。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` / `src/styles.css`：普通首屏在当前事实下方展示动作状态卡；页面继续把“路线”翻译成“行程”，不把 `marker/overlay` 术语放回普通用户首屏。
- `pc-tools/workstation/test/catalog.test.ts` / `test/App.test.ts`：补后端 summary 合同测试与前端首屏渲染测试。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录 `action_status_cards[]` 的只读边界。

## 验证结果

- 已通过定向后端测试：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`。
- 已通过定向前端首屏测试：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`。
- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `376 passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，新 PID 为 `84959`。
- 已通过 7001 live 只读 summary 验证：`action_status_cards` 返回 `camera_preview,map_preview,radar_map_points,nav2_route,keyboard_control,free_move,mapping_start`；卡片 JSON 不包含 `marker/overlay`；live 显示相机未显示且不是独占、地图已显示、地图雷达点未贴当前图、Nav2 可重跑复验、键盘可启用、自由移动可启动、建图启动未就绪且缺画面首帧/雷达新鲜。

## 剩余风险

- 本轮只新增只读摘要和首屏展示，不调用 Nav2 execute、manual、keyboard pulse、free-roam start/stop、map/radar lifecycle、delivery、stop 或 `/cmd_vel`。
- 真实运动、完整 Nav2 复验、wheel L/R 非零和建图启动仍需要现场安全确认后单独执行。
