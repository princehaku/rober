# PC 当前卡点直达入口

- sprint_type: micro
- 时间：2026-06-30 16:11 CST
- owner：User Touchpoint Full-Stack Engineer（单线闭环；本轮运行时不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlLiveClosureSummary` 新增 `primary_status_item_id` 和 `primary_status_source_card_id`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：按当前卡点状态派生主处理目标。轮速复验和送达缺口指向图上行程卡，画面/地图/雷达 WYSIWYG 缺口指向对应卡片，传感器缺口指向建图卡，安全确认缺口优先指向自由移动/键盘/行程入口。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`plain-live-closure-summary` 暴露主目标 DOM 字段，并新增 `plain-live-closure-go` 按钮。按钮只做页面内聚焦，不调用接口、不勾选安全确认、不发车。
- `pc-tools/workstation/test/App.test.ts`：默认首屏 fixture 和测试覆盖主目标字段与按钮不触发 fetch 的行为。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录当前卡点直达入口的只读定位口径。

## 验证结果

- 已通过：`npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`。
- 已通过：`npm test -- --run`（2 files / 397 tests passed）。
- 已通过：`npm run build`（`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`）。
- 已通过：`git diff --check`。
- 已执行：`npm run lint`，0 errors，保留既有 4 个 `RobotControlConsolePanel.vue` 换行 warning。
- 已通过：7001 刷新验证。旧 PID `88943` 已停止，新 Node PID `740` 监听 `TCP *:7001`；`GET /` 返回新 bundle `index-DCrA8ad_.js` / `index-BBcFFzNr.css`；`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 在当前 `status=needs_wheel_rerun` 下返回 `primary_status_item_id=nav2_route_execution`、`primary_status_source_card_id=nav2_route`、`next_action_source_card_id=nav2_route`、`sends_motion_when_clicked=false`。

## 剩余风险

- 该入口只解决 PC 普通首页“下一步去哪处理”的易用性；真实 Nav2 wheel raw L/R 非零、delivery success、相机首帧和雷达 fresh scan 仍需要现场硬件/运行时证据。
