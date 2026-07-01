# PC 路线重跑文案直达普通用户

sprint_type: micro

## 实际改动

- `live_motion_runbook_*_plain` 的 ready / primary / summary 文案改为优先使用 `display_label`，当 Nav2 已到点但同窗口 wheel L/R 未闭环时，普通用户看到 `重跑图上行程并复验轮速`，而不是笼统的 `完整行程执行`。
- `field_acceptance_remaining_operator_action_summary_plain` 和 `field_acceptance_parallel_status_plain` 同步使用 display label，现场并行动作摘要直接写明“安全确认后动作：重跑图上行程并复验轮速”。
- 保留兼容字段不变：`field_acceptance_primary_safety_confirm_ready_action_label`、`field_acceptance_next_step_label` 和 `field_acceptance_safety_confirm_ready_action_labels` 仍输出旧 label `完整行程执行`；新增行为只影响给人看的 plain 文案。
- 同步更新 `docs/product/pc_tools_workstation.md` 和 summary 单测期望。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts`：通过，10 tests passed。
- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：通过，3 files / 428 tests passed。
- `npm run lint`：通过。
- `git diff --check`：通过。
- `npm run build`：通过，Vite 仅保留既有 bundle size warning。
- 7001 已重启并监听 `*:7001`。
- `curl http://127.0.0.1:7001/api/robot-control/summary` 只读 smoke：`live_motion_runbook_ready_plain`、`live_motion_runbook_primary_action_plain`、`field_acceptance_parallel_status_plain` 和 `field_acceptance_remaining_operator_action_summary_plain` 均显示 `重跑图上行程并复验轮速`；旧 label 字段仍为 `完整行程执行`，display label 字段为 `重跑图上行程并复验轮速`。
- Chrome headless DOM smoke：`plain-field-acceptance-packet` 文案、`data-parallel-status-plain`、`data-next-step-display-label`、`data-primary-safety-confirm-ready-action-display-label` 和 `data-safety-confirm-ready-action-display-labels` 同步显示 `重跑图上行程并复验轮速`；兼容 `data-*-label` 仍保留 `完整行程执行`。

## 剩余风险

- 本轮没有新的现场安全确认，也没有发送任何 Nav2/manual/keyboard/free-roam/建图/stop 或 `/cmd_vel` 命令；wheel L/R 非零、delivery success、键盘连续运动、自由移动运行和建图启动仍需现场执行后复验。
- 当前相机仍提示 USB 12M full-speed，需要换高速 USB 口/线或带供电 Hub 后再做相机首帧复验；本轮只改 PC 文案/摘要，不处理物理链路。
