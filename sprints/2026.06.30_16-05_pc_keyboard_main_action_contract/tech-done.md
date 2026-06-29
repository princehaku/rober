# 2026.06.30 16:05 PC keyboard main action contract

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainKeyboardMainActionKind`、`plainKeyboardTargetSource`、`plainKeyboardMainActionSendsMotion`、`plainKeyboardArmSendsMotion`、`plainKeyboardRequiresHold` 和 `plainKeyboardMainActionSummary`。
  - 普通首屏键盘面板新增 DOM 证据：`data-main-action-kind`、`data-sends-motion-when-holding`、`data-arm-sends-motion`、`data-requires-hold-to-move`、`data-target-source`、`data-stop-triggers`。
  - 键盘启用按钮新增 `data-sends-motion-when-clicked=false` 和 `data-requires-hold-to-move=true`。
  - 自由移动屏幕方向键新增 `data-sends-motion-while-held` 和 `data-stop-trigger=pointerup,pointerleave,pointercancel`。
  - 普通首屏新增 `plain-keyboard-main-action-summary`，直接说明启用键盘不发车、只有按住方向键/WASD 才连续低速 pulse，松开/失焦/切页会 stop。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定未勾安全确认时键盘主动作不会发车。
  - 锁定安全确认后“启用键盘”只拿按键窗口，不发送 manual。
  - 锁定按住方向键后主动作进入 `holding_direction_sends_pulses`，才声明会发送连续 pulse。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步键盘连续控制主动作合同和 stop trigger 口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - 通过：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `cd pc-tools/workstation && npm test -- test/App.test.ts -t "reuses one plain safety confirmation for trip, keyboard, and free-roam mapping"`
  - 通过：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `cd pc-tools/workstation && npm test -- test/App.test.ts -t "allows confirmed low-speed motion when operator visual material is incomplete and still allows stop"`
  - 通过：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `cd pc-tools/workstation && npm test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `cd pc-tools/workstation && npm run build`
  - 通过：Vite build 成功；保留既有 `Some chunks are larger than 500 kB after minification` warning。
- `git diff --check`
  - 通过：无 whitespace error。

## 剩余风险

- 本轮只强化 PC 普通首屏键盘连续控制的点击/按住语义和 DOM 证据，没有触发真实 manual/stop、Nav2、free-roam 或 `/cmd_vel`。
- 目标仍未完全完成：真实完整 Nav2 路线执行、真实键盘连续控制、真实雷达贴图和建图闭环还需要继续现场验证。
