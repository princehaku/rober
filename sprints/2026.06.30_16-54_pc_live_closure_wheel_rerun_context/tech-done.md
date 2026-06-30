# PC Live Closure Wheel Rerun Context Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-summary` 和 `plain-live-closure-go` 新增 wheel rerun 上下文字段。
  - 暴露 `data-wheel-rerun-command-mode`、`data-last-base-command-mode`、`data-next-base-command-mode`、`data-wheel-feedback-status`、`data-latest-wheel-raw-left`、`data-latest-wheel-raw-right`。
  - 目的：当前卡点为 `needs_wheel_rerun` 时，现场脚本能直接读出上次/下次底盘模式和执行窗口 L/R，不把缺口误判成相机、雷达或页面导流问题。
- `pc-tools/workstation/test/App.test.ts`
  - 在 `needs_wheel_rerun` 场景锁定上次 `pwm`、下次 `ros`、L/R=`0/0`、`goal_succeeded_but_wheel_lr_zero` 等 DOM 字段。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明该合同只读，不执行 Nav2、不发送底盘命令。

## 验证结果

- `npm test -- test/App.test.ts -t "keeps live closure wheel rerun as a focus-only Nav2 action"`
  - 通过：`Test Files 1 passed (1)`，`Tests 1 passed | 223 skipped (224)`。
- `npm test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 398 passed (398)`。
- `npm run lint`
  - 通过：0 error，保留既有 `RobotControlConsolePanel.vue` 4 个 Vue multiline warning。
- `npm run build`
  - 通过：生成 `dist/assets/index-Dzwi1AwR.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`
  - 通过，无 whitespace 错误。
- 7001 重启与只读 smoke
  - 已重启 Node 到 `0.0.0.0:7001`，新 PID `83237`。
  - `GET http://127.0.0.1:7001/` 返回新 bundle `index-Dzwi1AwR.js`。
  - bundle 只读 grep 命中 `plain-live-closure-go`、`data-wheel-rerun-command-mode`、`data-last-base-command-mode`、`data-next-base-command-mode`、`data-wheel-feedback-status`、`data-latest-wheel-raw-left`、`data-latest-wheel-raw-right`。
  - `GET /api/robot-control/summary?base_url=http%3A%2F%2F192.168.1.11%3A8787` 为只读请求，未发送运动；返回 `live_status=needs_wheel_rerun`、`target=nav2_route`、`last=pwm`、`next=ros`、`wheel_status=goal_succeeded_but_wheel_lr_zero`、`L/R=0/0`。

## 剩余风险

- 本轮只补当前卡点的只读复验上下文，不执行真实 Nav2 重跑、不证明真实 wheel raw L/R 非零。
- 现场当前卡点仍为 `needs_wheel_rerun`，需要用户明确安全确认后在行程卡重跑图上行程，才能完成同窗口轮速 L/R 复验。
