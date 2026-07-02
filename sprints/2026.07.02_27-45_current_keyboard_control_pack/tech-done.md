# current_keyboard_control_pack

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 状态: 已完成

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`: 增加 `current_keyboard_control_pack_*` summary 合同字段，覆盖键盘连续手控当前验收包的入口、读回、缺口、按住移动和只读边界。
- `pc-tools/workstation/src/server/robotControlSummary.ts`: 从现有 `hold_keyboard` runbook 和 live closure summary 生成 `current_keyboard_control_pack_*` 顶层字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`: 新增 `plain-current-keyboard-control-pack` 普通 DOM 短行，显示“启用不发车、按住才动、松开后只读复验”。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`: 增加 summary 与 DOM 验收覆盖。
- `docs/product/pc_tools_workstation.md`: 同步 PC 键盘连续手控包和地图 ROS2 配套口径。

## 验证结果

- 通过: `npm test -- --run robotControlSummary.test.ts App.test.ts`
  - `Test Files 2 passed`
  - `Tests 247 passed`
- 通过: `npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍提示单包 chunk 大于 500 kB，这是既有前端体积提示，不影响本轮合同字段。
- 通过: `npm run lint`
  - `eslint .`
- 通过: `git diff --check`
- 通过: live `0.0.0.0:7001` summary readback
  - Node 重启后监听 `*:7001`。
  - `current_keyboard_control_pack_status=ready_for_safety_confirm`
  - `current_keyboard_control_pack_action_id=hold_keyboard`
  - `current_keyboard_control_pack_enable_sends_motion=false`
  - `current_keyboard_control_pack_hold_sends_motion=true`
  - `map_display_primary_tool=pc_big_map`
  - `map_display_primary_url=/map`
  - `map_display_ros2_companion_tools=[rviz2, foxglove]`

## 剩余风险

- 当前改动只补 PC summary/DOM 合同和本地/live 只读验证；真实小车按住键盘后的 wheel raw L/R 非零、松开后 stop 收口仍需要现场在安全确认后执行。
- 地图显示已经提供 `/map` 大屏、RViz2/Foxglove 工程观察口径；真实 RViz2/Foxglove 是否可用仍取决于上车 ROS2 环境和 bridge 是否启动。
