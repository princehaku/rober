# PC 目标检查汇总下一步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlGoalChecklistSummary` 和 `RobotControlSummaryResponse.goal_checklist_summary`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 基于同轮 `goal_checklist[]` 生成汇总：总项数、已完成数、剩余数、需要安全确认数、需要真实运动验证数、第一项未完成目标和下一步。
  - fail-closed 响应补默认 `goal_checklist_summary`，避免前端空形状。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“本轮目标检查”顶部新增汇总行和“去处理下一项”按钮。
  - 按钮只做页面内滚动/聚焦，不自动点击控件、不勾选安全确认、不触发任何控制接口。
- `pc-tools/workstation/src/styles.css`
  - 增加目标检查汇总行的紧凑响应式样式。
- `pc-tools/workstation/test/catalog.test.ts`
  - 验证 summary 的汇总字段、第一项未完成目标和禁止 `raw/marker/overlay`。
- `pc-tools/workstation/test/App.test.ts`
  - 验证普通首屏显示汇总，点击“去处理下一项”只聚焦，不新增 fetch 调用。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步记录 `goal_checklist_summary` 和无控制边界。

## 验证结果

- 已通过：
  - `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`
  - `npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`
  - `npm --prefix pc-tools/workstation test`
  - 结果：`2 passed`、`376 passed`
  - `npm --prefix pc-tools/workstation run build`
  - 结果：通过；仅保留既有 Vite chunk size warning。
- 运行验证：
  - PC API 已用新代码重启到 `HOST=0.0.0.0 PORT=7001`；实际监听 `*:7001` 的 Node PID 为 `6162`。
  - 只读 `GET http://127.0.0.1:7001/api/health` 通过，schema 为 `trashbot.pc_tools_workstation.health.v1`。
  - 只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 通过，`goal_checklist_summary.status=in_progress`，
    `done_count=1`、`remaining_count=6`、`first_incomplete_item_id=camera_wysiwyg`。
  - live `goal_checklist_summary` JSON 不包含 `raw`、`marker` 或 `overlay`。

## 剩余风险

- 本轮只新增只读汇总和下一步聚焦，不执行真实 Nav2、键盘连续手控、自由移动或建图。
- 完整目标仍需要现场安全确认后继续实车/HIL 验证。
