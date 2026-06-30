# PC Live Closure Focus Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-go` 当前卡点按钮补齐只聚焦不发车的 DOM 合同。
  - 按钮暴露目标 item/card、wheel rerun 状态、同窗口 L/R 复验要求、固定 Nav2 rerun endpoint 和固定 wheel readback endpoint。
  - 按钮明确 `data-focus-only=true`、`data-starts-nav2=false`、`data-starts-manual=false`、`data-starts-keyboard=false`、`data-sends-motion-when-clicked=false`。
- `pc-tools/workstation/test/App.test.ts`
  - 默认当前所见缺口场景锁定 current closure 按钮的 focus-only 合同。
  - 新增 `needs_wheel_rerun` 场景，验证当前卡点只聚焦 Nav2 行程卡，不调用 Nav2 execute、manual 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录当前卡点按钮的只读导流合同，明确轮速复验仍需用户在行程卡勾安全确认后执行。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default|keeps live closure wheel rerun as a focus-only Nav2 action"`
  - 通过：`Test Files 1 passed (1)`，`Tests 2 passed | 222 skipped (224)`。
- `npm test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 398 passed (398)`。
- `npm run lint`
  - 通过：0 error，保留既有 `RobotControlConsolePanel.vue` 4 个 Vue multiline warning。
- `npm run build`
  - 通过：生成 `dist/assets/index-MAL-ttmc.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`
  - 通过，无 whitespace 错误。
- 7001 重启与只读 smoke
  - 已重启 Node 到 `0.0.0.0:7001`，新 PID `59644`。
  - `GET http://127.0.0.1:7001/` 返回新 bundle `index-MAL-ttmc.js`。
  - bundle 只读 grep 命中 `plain-live-closure-go`、`data-focus-only`、`data-focus-target-source-card-id`、`data-fixed-wheel-rerun-endpoint`、`data-fixed-wheel-readback-endpoint`、`data-starts-nav2`、`data-starts-manual` 和 `data-starts-keyboard`。
  - `GET /api/robot-control/summary?base_url=http%3A%2F%2F192.168.1.11%3A8787` 为只读请求，未发送运动；返回 `live_status=needs_wheel_rerun`、`needs_wheel_rerun=true`、`target=nav2_route`。

## 剩余风险

- 本轮只补当前卡点按钮的只读导流合同，不执行真实 Nav2 重跑、不证明真实 wheel raw L/R 非零。
- 现场当前卡点仍为 `needs_wheel_rerun`，后续需要用户明确安全确认后在行程卡发起真实图上行程重跑，才能验证同窗口轮速 L/R。
