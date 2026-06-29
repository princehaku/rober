# PC 键盘方向按钮 DOM 合同

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-30 18:05 CST

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainKeyboardDirectionButtonEvidence`，把屏幕方向键的按住移动、松开/移出/取消停止、固定 manual/stop 代理、pulse 间隔和 pulse 时长整理成共用证据。
  - `keyboard-screen-forward/left/right/back` 新增 `data-direction`、`data-sends-motion-while-held`、`data-requires-hold-to-move`、`data-stop-trigger`、`data-fixed-keyboard-manual-endpoint`、`data-fixed-keyboard-stop-endpoint`、`data-pulse-interval-ms`、`data-pulse-duration-ms`。
  - `keyboard-screen-stop` 新增 `data-sends-motion-when-clicked=false`、`data-stop-trigger=click` 和 `data-fixed-keyboard-stop-endpoint`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展默认首屏测试，证明未勾安全确认时实际方向键不会发车，但已经暴露固定代理和 stop 合同。
  - 扩展键盘启用后的连续手控测试，证明四个方向键都会在可按住状态暴露固定 manual/stop endpoint、260ms 间隔、240ms pulse 和 pointer stop 合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 记录 2026-06-30 18:05 CST 的键盘方向按钮 DOM 合同。

## 验证结果

- 已通过:
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "stops screen keyboard control when the pointer is cancelled"`
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "stops screen keyboard control when the pointer leaves the button"`
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "stops continuous keyboard control when the window loses focus or the page is hidden"`
  - `cd pc-tools/workstation && npm run build`
    - 结果: TypeScript 与 Vite build 通过，生成 `dist/assets/index-DDJUx_6O.js` 和 `dist/assets/index-BZI7zFw0.css`
  - `cd pc-tools/workstation && npm test -- --run`
    - 结果: `Test Files 2 passed (2)`, `Tests 389 passed (389)`
  - `git diff --check`
    - 结果: 通过，无 whitespace error
  - 重启并验证 `0.0.0.0:7001`
    - 结果: `node` 监听 `TCP *:7001`
  - `curl -fsS http://127.0.0.1:7001/`
    - 结果: 返回 `Rober PC Tools Workstation`，资产为 `index-DDJUx_6O.js` / `index-BZI7zFw0.css`
  - `curl -fsS http://127.0.0.1:7001/assets/index-DDJUx_6O.js | rg ...`
    - 结果: 构建产物包含 `data-sends-motion-while-held`、`data-requires-hold-to-move`、`data-stop-trigger`、`data-fixed-keyboard-manual-endpoint`、`data-fixed-keyboard-stop-endpoint`、`data-pulse-interval-ms`、`data-pulse-duration-ms`
  - `GET http://127.0.0.1:7001/api/robot-control/summary`
    - 结果: HTTP 200，`schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，`keyboard_control_start_ready=true`，`keyboard_control_mode=bounded_repeating_manual_pulse`，manual/stop endpoint 为固定 PC 代理

## 剩余风险

- 本轮只补 PC 普通首屏实际方向键 DOM 合同和前端测试；没有向真实小车发送键盘 pulse 或 stop。
- 旧 artifact 文件仍有历史未提交改动，本轮不纳入提交范围。
