# 2026-06-23 17:20 Micro Sprint: fresh T1001 帧数从真实数组派生

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC summary 在读取 `/api/base/status.feedback_readback` 时，若没有显式 `t1001_feedback_frame_count`，会从 `t1001_feedback_frames[]` 数组长度派生 `latest_t1001_observed_count`。
  - 仍保留 `wheel_feedback_summary.frame_count` 作为次级 fallback；该计数只用于只读展示，不证明 wheel raw L/R 非零或真实运动。
- `pc-tools/workstation/test/catalog.test.ts`
  - 将 base status fresh count 测试改成真实上位机形态：只给 12 个 `t1001_feedback_frames`，不提供显式 count，确认 PC summary 仍显示 fresh `12`，并优先于 stale samples `3`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 fresh T1001 帧数的派生规则和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "Robot Control summary derives fresh base status T1001 frame count from frames array"`：通过，1 个测试文件通过，1 个相关用例通过。
- `cd pc-tools/workstation && npm test`：通过，2 个测试文件通过，142 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite build 完成，server/app TypeScript 均通过。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只修复 PC summary 的只读展示口径，不证明 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或 PC 键盘连续手控。
- 真实上位机当前仍显示雷达 lifecycle 未运行、wheel raw L/R 非零未证明、Nav2 latest 未证明、delivery 未成功；继续真实动作前仍需要现场 operator 明确确认。
