# 2026.06.30 15:35 PC Nav2 main action contract

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainTripMainActionKind`、`plainTripMainActionTargetSource`、`plainTripMainActionSendsMotion`、`plainTripManagedRuntimeWillAutostart` 和 `plainTripMainActionSummary`。
  - 普通首屏行程主按钮新增 DOM 证据：`data-main-action-kind`、`data-sends-motion-when-clicked`、`data-target-source`、`data-minimal-precheck-safety-only`、`data-managed-runtime-autostart`。
  - 行程卡新增可见短句 `plain-trip-main-action-summary`，直接说明当前点击是只准备/刷新路线、不发车，还是执行当前地图路线。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定未勾安全确认时主按钮不发车。
  - 锁定勾安全确认但无当前图上路线时，主按钮只走 no-motion 路线准备。
  - 锁定当前地图路线可见且需要重跑复验时，主按钮才是 `execute_current_map_route`，并声明会发送运动执行。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步行程主按钮点击语义和最小发车确认边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - 通过：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `cd pc-tools/workstation && npm test -- test/App.test.ts -t "reuses one plain safety confirmation for trip, keyboard, and free-roam mapping"`
  - 通过：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `cd pc-tools/workstation && npm test -- test/App.test.ts -t "keeps the summary-requested ROS rerun visible for an old PWM route with zero wheel readback"`
  - 通过：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `cd pc-tools/workstation && npm test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `cd pc-tools/workstation && npm run build`
  - 通过：Vite build 成功；保留既有 `Some chunks are larger than 500 kB after minification` warning。
- `git diff --check`
  - 通过：无 whitespace error。
- 7001 live 更新：
  - 已重启：`npm run api -- --host 0.0.0.0 --port 7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`。
  - `curl -fsS http://127.0.0.1:7001/` 通过，首页加载当前构建产物 `index-BC9juVgy.js`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 只读通过：HTTP 200，`schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，`nav2_status=ready_needs_wheel_rerun`，`nav2_minimal_precheck=true`，`card_count=7`。

## 剩余风险

- 本轮只强化 PC 普通首屏行程主按钮的真实点击语义和 DOM 证据，没有触发真实 Nav2 goal、manual、keyboard、free-roam、stop 或 `/cmd_vel`。
- 目标仍未完全完成：真实完整 Nav2 路线执行、真实键盘连续控制、真实雷达贴图和建图闭环还需要继续现场验证。
