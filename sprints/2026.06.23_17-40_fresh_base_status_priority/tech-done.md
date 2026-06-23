# 2026-06-23 17:40 Micro Sprint: fresh base/status 优先于 stale samples

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当 `/api/base/status` 本次 fresh readback 已读到 T1001 帧时，`readback_summary.base.latest_feedback_status` 改为 `fresh_base_status_readback`。
  - 嵌套 `feedback-samples/latest` 的 stale 状态仍保留在 endpoint key values；只是普通 summary 不再把它当作当前轮速状态。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 base status fresh frame count 测试，确认 fresh `/api/base/status` 优先于 stale samples。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏轮速测试，fresh base/status 下不再显示 `历史轮速样本已过期`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 fresh readback 优先级和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "Robot Control summary derives fresh base status T1001 frame count from frames array|shows current wheel L/R and frame count in plain goal progress from summary"`：通过，2 个测试文件通过，2 个相关用例通过。
- `cd pc-tools/workstation && npm test`：通过，2 个测试文件通过，142 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite build 完成，server/app TypeScript 均通过。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只修正 PC 只读展示优先级，不证明 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或 PC 键盘连续手控。
- 真实上位机仍显示雷达 lifecycle 未运行、wheel raw L/R 非零未证明、Nav2 latest 未证明、delivery 未成功；真实动作仍需现场 operator 明确确认。
