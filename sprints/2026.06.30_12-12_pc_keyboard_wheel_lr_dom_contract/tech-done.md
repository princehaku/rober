# PC 键盘 wheel raw L/R DOM 契约

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘连续手控根面板新增 `data-wheel-state`、`data-wheel-left`、`data-wheel-right`、`data-wheel-lr-nonzero-proven`。
  - 键盘轮速提示行新增同一组 DOM 字段，普通用户看到中文，测试和现场 smoke 可直接读结构化 L/R。
  - 地图上的自由移动/扫图方向 marker 新增 `data-wheel-left`、`data-wheel-right`、`data-wheel-lr-nonzero-proven`，让地图 marker 与键盘 wheel raw L/R 证据一致。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展自由移动键盘、扫图键盘、PC 键盘连续手控测试，确认 wheel raw L/R 和非零证明同时出现在键盘面板和地图方向 marker。

## 验证结果

- `npm test -- test/App.test.ts -t "free roam.*keyboard|runtime map preview|continuous keyboard control"`：通过，2 passed。
- `npm test -- test/App.test.ts -t "keeps keyboard pulses continuous"`：通过，1 passed。
- `npm test -- --run`：通过，2 test files、393 tests passed。
- `npm run lint`：通过，0 errors；保留既有 4 个 Vue multiline warning。
- `npm run build`：通过，产物 `dist/assets/index-BrleZEDU.js`。
- `git diff --check`：通过，无 whitespace 问题。
- 7001 重启：`npm run api` 后 `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node PID `29340` 监听 `*:7001`。
- 7001 只读 smoke：`curl 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787'` 返回 `trashbot.pc_tools_workstation.robot_control_summary.v1`；小车 API 读回仍有 `fetch_timeout_2400ms`，所以仅证明 PC Node 正常。

## 剩余风险

- 当前验证为 PC 端 mock/DOM 行为，未向真实小车发送键盘运动命令。
- 真实上车端如果 wheel raw L/R 字段名或时序漂移，仍需要现场只读 summary 和安全确认后的 HIL 验证复核。
