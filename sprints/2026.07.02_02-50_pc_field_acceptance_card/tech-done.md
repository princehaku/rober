# PC 现场验收卡

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `plain-live-closure-summary` 新增 `plain-field-acceptance-packet`。
  - 读取 `field_acceptance_packet` 后显示“现场验收”卡：下一步动作、是否需要先勾现场安全确认、是否会让车动、四个验收步骤状态和缺失证据。
  - 将英文证据 id 翻译成普通用户文案，例如“同窗口轮速 L/R 非零”“按住时轮速 L/R 非零”“送达确认”“画面首帧”“雷达新鲜读数”。
  - 所有卡片行按钮只做本页聚焦，固定声明不启动 Nav2/manual/keyboard/free-roam/建图、不提交 delivery、不 stop、不发送运动命令。
- `pc-tools/workstation/src/styles.css`
  - 新增现场验收卡的紧凑列表样式，保持普通用户首屏简易风格。
- `pc-tools/workstation/test/App.test.ts`
  - mock summary 补充 `field_acceptance_packet`，覆盖下一步动作、安全确认、缺失证据翻译和只读 DOM 边界。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏 `plain-field-acceptance-packet` UI 合同。

## 验证结果

- 已通过：`git diff --check`。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。Vite 仍提示单 bundle 超过 500 kB，这是既有体积警告，不影响本轮验收。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts test/catalog.test.ts -t "field acceptance|live-summary|robot control summary|Robot Control"`，49 passed。
- 已通过：`cd pc-tools/workstation && npm test`，3 files / 421 tests passed。
- 已通过：重启 PC workstation 到 `0.0.0.0:7001`，新 listener PID `29396`。
- 已通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `field_acceptance_next_step_id=run_nav2_route`、`field_acceptance_next_step_start_endpoint=/api/robot-control/nav2/goal/execute`、`field_acceptance_next_step_sends_motion=true`、`field_acceptance_next_step_requires_safety_confirm=true`、`field_acceptance_ready_step_ids=[run_nav2_route,hold_keyboard,start_free_move]`、`field_acceptance_blocked_step_ids=[start_mapping_when_sensors_ready]`、`field_acceptance_packet.sends_motion_when_clicked=false`、`field_acceptance_packet.starts_nav2_when_clicked=false`。
- 已通过：只读检查 `http://127.0.0.1:7001/assets/index-DmLRKDhQ.js`，bundle 包含 `plain-field-acceptance-packet`、`plain-field-acceptance-step` 和 `现场验收`。

## 剩余风险

- 本轮只改 PC 普通首屏展示和 DOM 合同，不执行真实 Nav2、键盘连续手控、自由移动或建图。
- 当前目标仍未完全收口：真实车还需要现场安全确认后执行 Nav2 路线、键盘按住窗口、自由移动读回，以及相机首帧 ready 后再启动建图。
