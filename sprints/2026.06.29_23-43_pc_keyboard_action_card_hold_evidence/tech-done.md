# 2026.06.29 23:43 PC 键盘连续手控动作卡证据

sprint_type: micro

## 设计先行

本轮只补 PC 键盘连续手控的结构化可验证合同，不新增控制入口。现有白话已经说明“按住才动、松开会停”，但外部脚本和 DOM smoke 需要稳定字段直接证明启用键盘不会发车、只有按住方向键/WASD 才发送低速短脉冲，以及停止触发项完整。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlActionStatusCard.evidence`，增加键盘连续手控字段：按住要求、启用是否发车、脉冲间隔/时长、命令模式、停止触发项、同窗口轮速验收要求。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `action_status_cards[].id=keyboard_control` 输出上述结构化证据。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通动作卡 DOM 增加只读 `data-hold-to-move-required`、`data-arm-sends-motion`、`data-requires-keydown-for-motion`、`data-pulse-interval-ms`、`data-pulse-duration-ms`、`data-manual-command-mode`、`data-stop-triggers`、`data-wheel-feedback-same-hold-window`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 summary API 中键盘动作卡的结构化证据。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通首屏 DOM 上能读到键盘连续手控合同。
- `pc-tools/README.md`
  - 同步记录只读字段合同和不发送控制命令边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`，1 passed / 167 skipped。
- 第一次过滤 `cd pc-tools/workstation && npm test -- test/App.test.ts -t "keeps the default first screen simple"` 未匹配测试名，结果为 218 skipped，不计为有效验证。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 passed / 217 skipped。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "keeps keyboard pulses continuous when summary refresh stalls during hold"`，1 passed / 217 skipped。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test -- --run`，386 passed。
- 通过：`git diff --check`。
- 通过：PC Node 已重启到 `0.0.0.0:7001`，只读 live spot check `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `keyboard_control.evidence.hold_to_move_required=true`、`arm_sends_motion=false`、`requires_keydown_for_motion=true`、`pulse_interval_ms=260`、`pulse_duration_ms=240`、`stop_triggers` 含 `key_released/window_blur/page_hidden/direction_changed/button_stop`。

## 剩余风险

- 本轮只补只读合同和 DOM 验证；live spot check 只读 summary，不启用键盘、不发送 manual pulse、不执行 Nav2/free-roam/delivery/stop 或 `/cmd_vel`。
- 键盘连续手控的真实 wheel L/R 非零仍需要现场安全确认后按住方向键复验。
