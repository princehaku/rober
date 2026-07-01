# PC 轮速 0/0 下一步卡

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainLiveWheelZeroNextStep` 计算属性。
  - 当 live 轮速仍为 `0/0` 且同窗口轮速未证明时，在当前卡点区显示 `plain-live-wheel-zero-next-step`。
  - 卡片明确展示：
    - 当前 L/R 为 `0/0`；
    - 影响完整 Nav2 路线与键盘连续手控验收；
    - 未勾安全确认时只引导到行程安全确认；
    - 已勾安全确认时才引导到图上路线执行按钮；
    - “只读复验”只刷新 map preview、Nav2 latest、base feedback samples、delivery latest 和 summary。
  - 所有按钮都固定 no-motion：不执行 Nav2、不发送 manual/keyboard/free-roam、不启动建图、不提交 delivery、不 stop。
- `pc-tools/workstation/src/styles.css`
  - 新增 `plain-live-wheel-zero-next-step` / `plain-live-wheel-zero-next-step-actions` 样式。
- `pc-tools/workstation/test/App.test.ts`
  - 补充轮速 0/0 卡片 DOM、文案、最小预检、no-motion 和聚焦不发请求测试。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-07-01 12:05 CST 起的轮速 0/0 下一步卡合同。

## 验证结果

- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：先失败一次，原因是新卡可见文案包含普通首屏禁词 `Nav2` / `路线`；已改为“完整图上行程”后通过，`1 passed | 230 skipped`。
- `npm run lint`：通过。
- `npm run build`：通过；仍有既有 Vite chunk size warning。
- `npm test`：通过，`3 passed / 417 tests passed`。
- `git diff --check`：通过。
- `GET http://127.0.0.1:7001/api/robot-control/summary` no-motion smoke：通过。当前 live summary 显示 `status=needs_wheel_rerun`、`needs_same_window_wheel_rerun=true`、`wheel_lr_nonzero_proven=false`、`wheel_rerun_latest_raw_left=0`、`wheel_rerun_latest_raw_right=0`、`route_ready_on_map=true`、`nav2_goal_succeeded=true`、`delivery_success=false`、`minimal_precheck_safety_only=true`。
- `GET http://127.0.0.1:7001/`：通过，HTTP 200，返回当前构建资源 `index-Cs694yd7.js` / `index-DMkCI5-t.css`。

## 剩余风险

- 本轮只改善 PC 对 `wheel raw L/R=0/0` 的下一步引导，不直接执行真实路线。
- 真实 wheel L/R 非零、delivery success、摄像头首帧和真实建图启动仍需要现场/上车证据继续闭环。
