# PC 键盘连续手控实时仪表

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainKeyboardTelemetrySummary`，把当前方向、当前按住 pulse 数、最佳连续 pulse 数、轮速 L/R、停止收口和按住时是否会发低速脉冲合成一行。
  - 键盘卡新增 `keyboard-telemetry-summary`，同步暴露 `data-current-direction`、`data-current-hold-pulse-count`、`data-best-continuous-pulse-count`、`data-wheel-state`、`data-stop-state`、`data-sends-motion-while-held` 和固定 manual/stop endpoint。
- `pc-tools/workstation/src/styles.css`
  - 给键盘仪表短行增加状态边框，让“手控中 / 已验证 / 停止失败”等状态在普通首屏更醒目。
- `pc-tools/workstation/test/App.test.ts`
  - 固定默认未启用、已启用等待按键、按住第 1 次 pulse、达到 2 次连续 pulse、松开后 stop 收口等仪表状态。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录键盘实时仪表和非控制变更边界。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `npm test -- test/App.test.ts -t "enables non-stop motion only after complete operator material and still uses the fixed workstation proxy"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `npm test -- --run`
  - 结果：通过，`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `npm run build`
  - 结果：通过，Vite 产物 `dist/assets/index-BpZE7S0q.css` 与 `dist/assets/index-Cxj94KDn.js` 已生成。
- `git diff --check`
  - 结果：通过，无空白错误。
- PC Node 重启与 HTTP smoke
  - `npm run api -- --host 0.0.0.0 --port 7001` 已重新监听，`lsof` 显示 `node` PID `61939` 监听 `TCP *:7001`。
  - `GET http://127.0.0.1:7001/` 返回新 bundle：`index-BpZE7S0q.css`、`index-Cxj94KDn.js`。

## 剩余风险

- 本轮只改 PC Web 显示、DOM 合同和文档，不改变键盘手控 gate，不自动启用键盘，也不额外发送 manual/stop 或 `/cmd_vel`。
- 真实车键盘连续手控仍需要现场 HIL 证明 wheel raw L/R 非零和 stop 收口；本轮提供的是 PC 侧更清晰的现场读数与脚本验收入口。
