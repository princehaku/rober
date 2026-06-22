# 2026-06-22 18:23 Wheel Stale Feedback Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：从上位机 `feedback_samples_latest.freshness` 中提炼 `feedback_samples_freshness_status` 与 `feedback_samples_age_ms`，并让 `readback_summary.base.latest_feedback_status` 优先反映 freshness 状态。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏轮速读回摘要在 latest sample 为 `stale` 时提示“历史轮速样本已过期，以当前读回为准”。
- `pc-tools/workstation/test/catalog.test.ts`：覆盖 stale latest sample 不覆盖 fresh `/api/base/status`，同时验证 summary 暴露 stale 状态。
- `pc-tools/workstation/test/App.test.ts`：覆盖普通轮速记录面板显示 stale 样本提示。
- `docs/product/pc_tools_workstation.md`：同步记录该提示只解释读回新旧关系，不触发任何运动或送达确认。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 普通首屏对 stale wheel feedback artifact 的解释；真实 wheel raw L/R 非零仍需要现场低速试动窗口读到同帧 T1001 非零并保存 operator report。
- 当前真实只读状态显示 `/api/base/status` 新鲜读回仍为 L/R=0/0，feedback sample latest 为 stale；这不是完成 wheel raw L/R 非零。
- Nav2 latest 已读到 `goal_succeeded`，delivery latest 仍为 false；delivery success 和 PC 键盘连续手控仍需要现场最终确认/材料 gate。
