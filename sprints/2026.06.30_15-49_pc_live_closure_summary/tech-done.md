# PC 当前卡点汇总

- sprint_type: micro
- 时间：2026-06-30 15:49 CST
- owner：User Touchpoint Full-Stack Engineer（单线闭环；本轮运行时不再调用 subagent）

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增 `RobotControlLiveClosureSummary` 契约，并挂到 `RobotControlSummaryResponse.live_closure_summary`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从 action cards、goal checklist、safe boundary 和 operator HIL material 只读派生 `live_closure_summary`，集中输出路线 ready、Nav2 action 成功、同窗口 wheel raw L/R、delivery success、画面/地图/雷达 WYSIWYG、自由移动、建图和最小安全确认状态。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`、`pc-tools/workstation/src/styles.css`：普通首屏新增 `plain-live-closure-summary` 当前卡点块，放在“现在可以做什么”和“当前所见”之间；该块只读，固定 `data-sends-motion-when-clicked=false`。
- `pc-tools/workstation/test/App.test.ts`：默认 Robot Control fixture 和首屏测试补齐当前卡点 DOM 验收。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录 `live_closure_summary` 和 `plain-live-closure-summary` 的只读合同。

## 验证结果

- 已通过：`npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`。
- 已通过：`npm test -- --run`（2 files / 397 tests passed）。
- 已通过：`npm run build`（`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`）。
- 已通过：`git diff --check`。
- 已执行：`npm run lint`，0 errors，保留既有 4 个 `RobotControlConsolePanel.vue` 换行 warning。
- 已通过：7001 刷新验证。旧 PID `45157` 已停止，新 Node PID `64115` 监听 `TCP *:7001`；`GET /` 返回新 bundle `index-BuhPH8_w.js` / `index-BBcFFzNr.css`；`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `live_closure_summary.status=needs_wheel_rerun`、`route_ready_on_map=true`、`nav2_goal_succeeded=true`、`wheel_lr_nonzero_proven=false`、`needs_same_window_wheel_rerun=true`、`delivery_success=false`、`map_current_visible=true`、`free_move_start_ready=true`、`minimal_precheck_safety_only=true`、`sends_motion_when_clicked=false`。

## 剩余风险

- 本轮未发送任何真实运动命令；Nav2 完整路线、wheel raw L/R 非零和 delivery success 的真实闭环仍需要现场在勾选安全确认后执行并复验。
