# Nav2 Post Execute Readback Aliases

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`GET /api/robot-control/summary` 顶层新增 `nav2_post_execute_readback_*` 短字段，明确完整图上路线执行成功后的自动复验顺序为地图画面、Nav2 latest、轮速采样、delivery latest 和 summary；同时暴露该复验链不发车、不启动控制、不提交送达。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐 `RobotControlSummaryResponse` 类型字段，避免前后端和测试脚本各自猜字段形状。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏行程卡、执行按钮和闭环读回按钮同步暴露 `data-nav2-post-execute-readback-*`，现场 DOM smoke 可直接确认执行后自动复验链覆盖完整 Nav2 路线闭环。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：锁住 summary 与 DOM 的 post-execute readback alias、顺序标签和只读边界。
- `docs/product/pc_tools_workstation.md`：同步产品合同，说明这些字段只描述执行后的只读复验，不改变发车安全确认或送达提交逻辑。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed`，`247 passed`。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍有既有 large chunk warning。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check`：通过，无空白错误。

## 剩余风险

- 本轮不执行真实 Nav2 goal，不发送 manual/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`；真实 wheel L/R 非零和 delivery success 仍需现场安全确认后实车复验。
- 该改动只补 PC 可读证据和 DOM 合同，不改变上车端 Nav2 控制器、底盘模式或传感器硬件状态。
