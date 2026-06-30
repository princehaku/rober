# PC Nav2 Plain Live Closure

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `live_closure_summary.status=needs_wheel_rerun` 时，API 源头的 `summary_plain` 和 `next_action_plain` 改为“同窗口轮速 L/R”普通文案。
  - 结构化字段、固定执行 endpoint 和同窗口轮速 L/R 非零验收口径不变。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加 `live_closure_summary` API 文案不包含 `wheel raw` 的回归断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 记录 Nav2 当前卡点 API 直接给普通用户文案的合同。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，3 tests。
- `npm test -- App.test.ts`：通过，225 tests。
- `npm test -- catalog.test.ts`：通过，174 tests。
- `npm test -- --run`：通过，402 tests。
- `npm run lint`：通过，保留既有 4 个 Vue multiline warning，无 error。
- `npm run build`：通过，保留既有 Vite chunk size warning。
- `git diff --check`：通过。
- 7001 只读 smoke：`live_closure_summary.summary_plain + next_action_plain` 中 `wheel raw` 为 false，状态仍为 `needs_wheel_rerun`，固定执行 endpoint 仍是 `/api/robot-control/nav2/goal/execute`，`sends_motion_when_clicked=false`。

## 剩余风险

- 本轮只改 PC/API 普通文案，没有发送 live motion/control POST。
- 完整 Nav2 路线执行仍需要现场勾选安全确认后重跑，并在同一执行窗口读到轮速 L/R 非零。
