# PC ready 运动动作卡组

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：在普通首屏动作清单的现场执行条下新增 `plain-live-ready-motion-actions`，把当前 ready 的图上行程、键盘连续手控、自由移动拆成独立小卡。每张卡只聚焦到目标卡片，不执行动作；真实发车/按住/自由移动仍必须由现场人员在对应卡片显式触发。
- `pc-tools/workstation/src/styles.css`：新增 ready 动作卡组样式，保持紧凑可扫读。
- `pc-tools/workstation/test/App.test.ts`：补充 ready 动作卡 DOM 和 no-motion 点击测试，锁定“点击卡片按钮只 focus、不新增 fetch”的边界。
- `docs/product/pc_tools_workstation.md`：同步记录 ready 动作卡组合同。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，`1 passed | 230 skipped`。
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，`7 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 构建通过；仍有既有 chunk size warning。
- 通过：`npm test`，`3 passed / 417 passed`。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `*:7001`，进程 `node ... src/server/index.ts` PID `87576`；只读 `GET http://127.0.0.1:7001/map` 返回 `200`，加载新 assets `index-DgcgoZAt.js` / `index-Bl7C8gSH.css`。
- 通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `ready_actions=[run_nav2_route, hold_keyboard, start_free_move]`、`blocked_actions=[start_mapping_when_sensors_ready]`、`route_ready=true`、`nav2_goal_succeeded=true`、`wheel_lr_nonzero=false`、`keyboard_ready=true`、`free_move_start_ready=true`、`mapping_start_ready=false`。

## 剩余风险

- 本轮只改善 ready 动作导流，不发送任何运动/control POST。真实 Nav2 重跑、键盘按住和自由移动仍需要现场勾安全确认后显式触发，并在同窗口读回 wheel L/R、stop、delivery/free-roam latest 等材料。
