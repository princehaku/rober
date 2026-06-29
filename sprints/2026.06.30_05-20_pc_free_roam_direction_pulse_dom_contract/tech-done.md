# PC 自由移动方向键连续 Pulse DOM 合同

- sprint_type: micro
- 时间：2026-06-30 05:20 CST
- owner：User Touchpoint Full-Stack Engineer（主会话直接执行；本轮按用户要求不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“自由移动 / 建图”的四个屏幕方向按钮复用主键盘方向按钮的连续控制证据。
  - 新增/补齐 `data-direction`、`data-requires-hold-to-move`、`data-fixed-keyboard-manual-endpoint`、
    `data-fixed-keyboard-stop-endpoint`、`data-pulse-interval-ms`、`data-pulse-duration-ms`、
    `data-current-hold-pulse-count`、`data-best-continuous-pulse-count`、
    `data-verified-min-forwarded-pulses`、`data-same-hold-window-required`、
    `data-stop-required-after-hold`、`data-stop-settled-after-pulse`。
  - 自由移动方向区的停止按钮补齐 `data-sends-motion-when-clicked=false`、`data-stop-trigger=click` 和固定 stop endpoint。
- `pc-tools/workstation/test/App.test.ts`
  - 在自由移动/扫图流程中断言方向按钮初始不发车、按住后 pulse 计数递增、同一按住窗口达到 2 次、松开后当前计数归零且最佳连续计数保留。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录自由移动方向按钮连续控制 DOM 合同和只读边界。

## 验证结果

- 通过：`npm test -- test/App.test.ts -t "keeps free-roam keyboard locked until map recording starts"`，1 passed。
- 通过：`npm test -- --run`，`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 通过：`npm run build`，产物包含 `dist/assets/index-BgBImr9U.js` 和 `dist/assets/index-CZMHo-c5.css`。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，`lsof` 显示 `node` PID 3709 监听 `TCP *:7001`。
- 通过：只读 HTTP smoke，`GET http://127.0.0.1:7001/` 加载 `/assets/index-BgBImr9U.js`；
  bundle 中确认包含 `plain-free-roam-screen-forward`、`data-current-hold-pulse-count`、
  `data-stop-settled-after-pulse`、`data-fixed-keyboard-manual-endpoint`、`data-same-hold-window-required`。

## 剩余风险

- 本轮是 PC DOM/测试合同增强，没有真实小车 HIL 验证；真实自由移动仍需现场安全确认、停止兜底和同窗口 wheel raw L/R 非零证明。
- 这次不改变运动命令路径；方向按钮仍只在用户按住时通过既有 `/api/robot-control/base/manual` 代理发低速 pulse。
- 历史未暂存 artifact 文件保留原状，本轮不回滚不提交。
