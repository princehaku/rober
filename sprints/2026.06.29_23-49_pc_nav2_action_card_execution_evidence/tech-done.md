# 2026.06.29 23:49 PC Nav2 行程动作卡执行证据

sprint_type: micro

## 设计先行

本轮只补 PC 行程动作卡的结构化只读证据，不改变发车按钮行为。目标是让脚本和 DOM smoke 直接证明三件事：发车前最小门禁只剩现场安全确认；只有图上路线 ready 后执行才会进入运动；完整路线验收必须读取同窗口执行窗口轮速 L/R 非零。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlActionStatusCard.evidence`，增加 Nav2 行程执行证据字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `action_status_cards[].id=nav2_route` 输出路线 ready、最小安全确认、固定执行代理、运动发送边界、轮速验收、上次/下次底盘命令模式、托管 runtime autostart 和 blocker 数组。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通动作卡兼容旧 summary，从 `safe_command_boundary` / `readback_summary.nav2` 补 Nav2 只读证据，并暴露对应 DOM `data-*` 属性。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 summary API 中 `nav2_route.evidence`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通首屏 DOM 上能读到 Nav2 最小门禁和同窗口轮速验收合同。
- `pc-tools/README.md`
  - 同步记录只读字段合同和不发送控制命令边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`，1 passed / 167 skipped。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 passed / 217 skipped。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test -- --run`，386 passed。
- 通过：`git diff --check`。
- 通过：PC Node 已重启到 `0.0.0.0:7001`，只读 live spot check `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `nav2_route.evidence.route_ready_on_map=true`、`minimal_precheck_safety_only=true`、`execute_sends_motion_when_ready=true`、`wheel_feedback_status=goal_succeeded_but_wheel_lr_zero`、`last_base_command_mode=pwm`、`next_base_command_mode=ros`、`blockers=[]`。

## 剩余风险

- 本轮只补只读合同和 DOM 验证；live spot check 只读 summary，不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 完整 Nav2 路线真实执行和同窗口轮速 L/R 非零仍需要现场安全确认后复验。
