# Free Move Post Start Readback Aliases

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 顶层新增 `free_move_post_start_readback_*` 和 `current_free_move_action_post_start_readback_*` 字段，明确自由移动启动成功后的验收读回顺序为 free-roam latest、map preview、summary，并固定只读边界。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐 `RobotControlSummaryResponse` 类型，避免前端、脚本和测试分别猜字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-free-move-acceptance-proof` DOM 暴露 post-start readback endpoints、中文标签和只读 flags。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：锁住 API 与 DOM 的自由移动启动后读回链路。
- `docs/product/pc_tools_workstation.md`：同步产品合同，强调相机/雷达不作为自由移动发车前置，传感器 ready 才影响建图。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed`，`247 passed`。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍有既有 large chunk warning。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check`：通过，无空白错误。

## 剩余风险

- 本轮只补 PC/API/DOM 验收证据，不执行真实自由移动 start，不发送 Nav2/manual/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`。
- 真实低速自由移动和建图仍需现场勾安全确认后实车复验；相机首帧/雷达新鲜仍是建图 readiness，不是自由移动发车前置。
