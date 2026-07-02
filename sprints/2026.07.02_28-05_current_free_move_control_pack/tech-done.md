# current_free_move_control_pack

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 状态: 已完成

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`: 增加 `current_free_move_control_pack_*` summary 合同字段，覆盖自由移动当前验收包的入口、读回、缺口、建图 readiness 和边界。
- `pc-tools/workstation/src/server/robotControlSummary.ts`: 从现有 `start_free_move` runbook 和 live closure summary 生成自由移动当前包。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`: 新增 `plain-current-free-move-control-pack` 普通 DOM 短行。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`: 增加 summary 与 DOM 验收覆盖。
- `docs/product/pc_tools_workstation.md`: 同步 PC 自由移动当前包说明。

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
  - `current_free_move_control_pack_status=ready_for_safety_confirm`
  - `current_free_move_control_pack_action_id=start_free_move`
  - `current_free_move_control_pack_ready=true`
  - `current_free_move_control_pack_sends_motion_when_clicked=false`
  - `current_free_move_control_pack_sends_motion_when_executed=true`
  - `current_free_move_control_pack_starts_free_roam_when_executed=true`
  - `current_free_move_control_pack_readback_sends_motion=false`
  - `current_free_move_control_pack_mapping_start_missing_reasons=[camera_first_frame]`

## 剩余风险

- 当前改动只补 PC summary/DOM 合同和本地/live 只读验证；真实自由移动启动后的 `free_roam_latest_motion_ready` 仍需要现场勾安全确认后执行。
- 建图启动仍受相机首帧和雷达 WYSIWYG readiness 约束；自由移动本身不依赖相机或雷达。
