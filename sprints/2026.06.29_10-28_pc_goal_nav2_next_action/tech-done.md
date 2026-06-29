# PC Goal Nav2 Next Action

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/shared/contracts.ts` 为 `goal_checklist_summary` 增加 Nav2 行程专用字段：
  `nav2_item_id`、`nav2_source_card_id`、`nav2_next_action_plain`、`nav2_summary_plain`。
- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中把完整图上行程状态从总目标缺口、移动优先和建图摘要中单独拆出。
  当图上行程需要复验时，summary 会直接说明发车前只需行程安全确认，并给出轮速 L/R 闭环下一步。
- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 与 `src/styles.css` 中让普通首屏目标汇总显示 Nav2 摘要，
  并新增“去跑行程”按钮。按钮只做 scroll/focus，不自动勾选、不执行 Nav2。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：
  `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`
  - 结果：1 个文件通过，1 个测试通过，160 个跳过。
- 通过：
  `npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`
  - 结果：1 个文件通过，1 个测试通过，214 个跳过。
- 通过：
  `npm --prefix pc-tools/workstation test`
  - 结果：2 个文件通过，376 个测试通过。
- 通过：
  `npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript、Vite client build、server TypeScript 通过；仅保留既有 Vite chunk size warning。
- 通过 PC API 只读 live 验证：
  - `HOST=0.0.0.0 PORT=7001 npm --prefix pc-tools/workstation run api` 已启动，监听 PID `16992`。
  - `curl -fsS http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `nav2_item_id=nav2_route_execution`、
    `nav2_source_card_id=nav2_route`，`nav2_summary_plain` 显示“完整图上行程可复验；发车前只需要行程安全确认”。
  - live 验证只读 summary/health；未调用 manual、Nav2、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 剩余风险

- 真实 Nav2 复验仍需要现场勾选安全确认后手动点击；本轮只改善普通首屏的只读摘要和焦点引导。
