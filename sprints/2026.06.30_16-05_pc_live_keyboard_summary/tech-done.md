# PC 当前卡点键盘连续手控字段

- sprint_type: micro
- 时间：2026-06-30 16:05 CST
- owner：User Touchpoint Full-Stack Engineer（单线闭环；本轮运行时不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlLiveClosureSummary` 新增键盘连续手控字段，包括启动 ready、continuous ready、hold-to-move、enabled、motion verified、stop settled、连续 pulse 计数、验收阈值和 manual command mode。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从同轮 keyboard action card 与 readback 派生上述键盘字段，保持只读，不新增任何控制入口。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`plain-live-closure-summary` DOM 同步暴露 `data-keyboard-*` 字段，便于普通 PC 首页和自动脚本直接确认键盘连续手控当前合同。
- `pc-tools/workstation/test/App.test.ts`：默认 Robot Control 首屏 fixture 和断言覆盖键盘连续手控字段。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步当前卡点汇总的键盘字段合同。

## 验证结果

- 已通过：`npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`。
- 已通过：`npm test -- --run`（2 files / 397 tests passed）。
- 已通过：`npm run build`（`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`）。
- 已通过：`git diff --check`。
- 已执行：`npm run lint`，0 errors，保留既有 4 个 `RobotControlConsolePanel.vue` 换行 warning。
- 已通过：7001 刷新验证。旧 PID `77526` 已停止，新 Node PID `88943` 监听 `TCP *:7001`；`GET /` 返回新 bundle `index-ou9vU0j0.js` / `index-BBcFFzNr.css`；`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `live_closure_summary.keyboard_control_start_ready=true`、`keyboard_continuous_control_ready=true`、`keyboard_hold_to_move_required=true`、`keyboard_enabled=false`、`keyboard_motion_verified=false`、`keyboard_stop_settled_after_pulse=false`、`keyboard_best_continuous_pulse_count=0`、`keyboard_verified_min_forwarded_pulses=2`、`keyboard_manual_command_mode=ros`、`sends_motion_when_clicked=false`。

## 剩余风险

- 该改动只让 PC 当前卡点汇总暴露键盘连续手控 ready/合同字段；真实键盘连续手控完成仍需要现场勾安全确认后按住方向键/WASD，并在同一次按住窗口读到连续 pulse、wheel L/R 非零和 stop 收口。
