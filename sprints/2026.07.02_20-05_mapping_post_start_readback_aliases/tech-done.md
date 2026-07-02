# Mapping Post Start Readback Aliases

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 顶层新增 `mapping_post_start_readback_*` 和 `current_mapping_action_post_start_readback_*` 字段，固定建图启动成功后的只读复验顺序为 free-roam latest、map preview、summary。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐 `RobotControlSummaryResponse` 类型，避免前端、脚本和测试分别猜建图 post-start 读回合同。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-current-mapping-action` DOM 暴露 post-start readback endpoints、中文标签和只读边界 flags。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：锁住 API 与 DOM 的建图启动后读回链路。
- `docs/product/pc_tools_workstation.md`：同步产品合同，强调建图动作成功后的读回链只读，不再次启动 free-roam、建图 runtime、Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed`，`247 passed`。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍保留既有 large chunk warning。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check`：通过，无空白错误。

## 剩余风险

- 本轮只补 PC/API/DOM 验收证据，不执行真实 `/api/robot-control/map/start`，不发送 Nav2/manual/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`。
- 真实建图启动仍需要现场相机首帧和雷达新鲜 ready，并在勾选安全确认后上车复验。
