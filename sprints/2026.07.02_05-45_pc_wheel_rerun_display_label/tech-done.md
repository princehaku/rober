# PC 轮速重跑展示名补强

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为现场验收包、runbook、缺口归属和 Nav2 route acceptance packet 增加可选 `display_label` / display alias，保留旧 `label` 兼容字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：当完整行程已到点但同窗口 wheel L/R 仍未非零闭环时，新增普通用户展示名 `重跑图上行程并复验轮速`，并同步到 summary 顶层、field acceptance packet、missing evidence 和 Nav2 route acceptance packet。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：现场验收、主下一步、缺口归属、行程闭环卡和 DOM smoke 属性优先展示 display label，同时保留旧 label。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：补充 display label 合同和 DOM 可见文案断言。
- `docs/product/pc_tools_workstation.md`：同步现场验收 display label 合同，明确该字段只改变可见文案，不改变动作、端点或安全确认逻辑。

## 验证结果

- 通过：`npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`，428 tests passed。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`；只读 summary smoke 读到 `field_acceptance_next_step_display_label=重跑图上行程并复验轮速`、旧 `field_acceptance_next_step_label=完整行程执行`、`field_acceptance_packet.sends_motion_when_clicked=false`。
- 通过：浏览器 DOM smoke 读到 `plain-field-acceptance-packet`、`plain-field-acceptance-primary` 和 `plain-trip-closure-readback` 都存在；`data-next-step-display-label`、primary `data-display-label`、trip `data-display-label` 均为 `重跑图上行程并复验轮速`，且页面文本包含该展示名。

## 剩余风险

- 当前变更不触发真实小车运动，也不补 wheel L/R 非零真实 HIL 证据；现场仍需勾安全确认后重跑图上路线，才能完成 `same_window_wheel_lr_nonzero` 和送达确认闭环。
