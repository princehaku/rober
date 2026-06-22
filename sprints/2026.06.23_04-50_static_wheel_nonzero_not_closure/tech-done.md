# 2026-06-23 04:50 static wheel nonzero not closure

sprint_type: micro

## 实际改动

- 收紧 PC 高级 `目标收口进度` 的 wheel raw L/R 判定：只读 `/api/robot-control/base/feedback-samples` 即使读到 `wheel_feedback_lr_nonzero_proven=true`，也不再把 `wheel raw L/R 非零` 标为已满足。
- 新增前端回归测试，覆盖只读 samples 返回 `L/R=0.08/0.08`、`sends_motion_commands=false` 时，普通首屏只显示提示，保存轮速按钮保持禁用，且不调用 operator report、manual、delivery complete 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md`，明确只读非零采样不是 wheel 收口证据，收口仍要求本轮试动窗口或带 ref 的 operator report 材料。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test`，`Test Files 2 passed (2)`，`Tests 134 passed (134)`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`，Vite client build 和 server TypeScript build 均完成。
- 已通过：`git diff --check`。
- 测试期间两个历史 DOM smoke JSON 只改动 `checked_at`，已还原为原始时间戳，未纳入本轮 diff。

## 剩余风险

- 本轮是 PC 前端和测试口径收紧，不包含真实小车低速试动；因此不证明 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或 PC 键盘连续手控的现场闭环。
