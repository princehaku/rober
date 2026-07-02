# current_mapping_control_pack

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 状态: 已完成

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`: 增加 `current_mapping_control_pack_*` summary 合同字段，覆盖建图当前验收包的入口、读回、传感器 ready、WYSIWYG、自由移动边界和执行边界。
- `pc-tools/workstation/src/server/robotControlSummary.ts`: 从现有 `start_mapping_when_sensors_ready` runbook 和 live closure summary 生成建图当前包。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`: 新增 `plain-current-mapping-control-pack` 普通 DOM 短行。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`: 增加 summary 与 DOM 验收覆盖。
- `docs/product/pc_tools_workstation.md`: 同步 PC 建图当前包说明。

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
  - `current_mapping_control_pack_status=blocked`
  - `current_mapping_control_pack_camera_ready=false`
  - `current_mapping_control_pack_radar_ready=true`
  - `current_mapping_control_pack_missing_evidence=[camera_first_frame]`
  - `current_mapping_control_pack_blocks_free_move=false`
  - `current_mapping_control_pack_free_move_allowed_while_blocked=true`
  - `current_mapping_control_pack_sends_motion_when_clicked=false`
  - `current_mapping_control_pack_starts_map_runtime_when_executed=true`

## 剩余风险

- 当前改动只补 PC summary/DOM 合同和本地/live 只读验证；真实建图启动仍需要现场摄像头首帧与雷达新鲜同时 ready 后，勾安全确认执行。
- live 当前雷达已满足建图 readiness，但相机首帧仍阻塞建图；自由移动仍可在安全确认后先启动。
