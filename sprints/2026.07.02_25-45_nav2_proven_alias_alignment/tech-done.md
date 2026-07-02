# Nav2 Proven Alias Alignment

## sprint_type

micro

## 实际改动

- 用只读 SSH 和 PC 7001 读数复核当前真实状态：上位机可连，PC summary 显示完整行程还差 `same_window_wheel_lr_nonzero` 与 `delivery_success`，但 summary 顶层 `nav2_goal_execution_proven` 曾与 Nav2 latest 的 `not_proven` 口径不一致。
- 修正 `buildLiveClosureSummary` 的 Nav2 口径：`nav2_goal_succeeded` 表示 Nav2 action 到点成功，`nav2_goal_execution_proven` 只在同窗口 wheel L/R 非零后才为 true。
- 修正完整行程缺口数组，避免 wheel L/R 未闭环时误把 `nav2_goal_succeeded` 继续列为缺口。
- 更新 `robotControlSummary` 测试和产品文档，锁定 summary 与 latest 的 proven alias 一致性。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts`，结果 `Test Files 1 passed (1)`、`Tests 10 passed (10)`。
- 通过：`cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts`，结果 `Test Files 2 passed (2)`、`Tests 419 passed (419)`。
- 通过：`git diff --check`，无空白错误输出。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 与 `vite build` 完成；Vite 保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`，ESLint 无错误输出。

## 剩余风险

- 本轮真实上位机验证只读，不执行 Nav2、不发送手控、不启动 free-roam 或建图；完整 HIL 发车、同窗口 wheel L/R 非零和 delivery success 仍需现场安全确认后执行。
