# PC Nav2 行程主面板 DOM 合同

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-30 17:45 CST

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainTripDomEvidence`，把当前地图路线、源路线点数、执行按钮语义、最小安全确认、托管 runtime、执行窗口 wheel raw L/R 复验和固定执行代理整理成主面板 DOM 证据。
  - `plain-trip-run` 主面板新增 `data-route-point-count`、`data-route-source-point-count`、`data-current-route-visible`、`data-recent-route-visible`、`data-robot-pose-visible`、`data-map-wysiwyg-pending`、`data-route-wysiwyg-ready`、`data-main-action-kind`、`data-target-source`、`data-sends-motion-when-clicked`、`data-main-action-can-run`、`data-managed-runtime-autostart`、`data-requires-same-window-wheel-lr-nonzero`、`data-wheel-lr-nonzero-proven`、`data-latest-wheel-raw-left`、`data-latest-wheel-raw-right`、`data-last-base-command-mode`、`data-next-base-command-mode` 和 `data-fixed-execute-proxy-endpoint`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展未勾安全确认、路线已准备但未贴图、当前地图路线可执行、Nav2 runtime 停止但执行会托管启动四类断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 记录 2026-06-30 17:45 CST 的行程主面板 DOM 合同。

## 验证结果

- 已通过:
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "runs plain trip preflight and execution only after the safety checkbox is checked"`
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "shows a summary route on the initial map preview when route coordinates are available"`
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "lets a ready route execute through managed Nav2 runtime when lifecycle is stopped"`
  - `cd pc-tools/workstation && npm test -- --run`
    - 结果: `Test Files 2 passed (2)`, `Tests 389 passed (389)`
  - `cd pc-tools/workstation && npm run build`
    - 结果: TypeScript 与 Vite build 通过，生成 `dist/assets/index-DOOgUgwj.js` 和 `dist/assets/index-BZI7zFw0.css`
  - `git diff --check`
    - 结果: 通过，无 whitespace error
  - 重启并验证 `0.0.0.0:7001`
    - 结果: `node` 监听 `TCP *:7001`
  - `curl -fsS http://127.0.0.1:7001/`
    - 结果: 返回 `Rober PC Tools Workstation`，资产为 `index-DOOgUgwj.js` / `index-BZI7zFw0.css`
  - `curl -fsS http://127.0.0.1:7001/assets/index-DOOgUgwj.js | rg ...`
    - 结果: 构建产物包含 `data-route-source-point-count`、`data-current-route-visible`、`data-route-wysiwyg-ready`、`data-fixed-execute-proxy-endpoint`、`data-requires-same-window-wheel-lr-nonzero`、`data-wheel-lr-nonzero-proven`
  - `GET http://127.0.0.1:7001/api/robot-control/summary`
    - 结果: HTTP 200，`schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，`nav2_goal_ready=true`，`nav2_goal_blockers=[]`，`nav2_goal_wheel_feedback_status=goal_succeeded_but_wheel_lr_zero`

## 剩余风险

- 本轮只补 PC 普通首屏 DOM 合同和前端测试；没有对真实小车发送 Nav2 goal，也没有证明真实 HIL 的完整路线执行、底盘 wheel raw L/R 非零或送达成功。
- 旧 artifact 文件仍有历史未提交改动，本轮不纳入提交范围。
