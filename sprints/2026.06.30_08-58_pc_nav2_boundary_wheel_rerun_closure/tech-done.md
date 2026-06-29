# PC Nav2 边界下一步补轮速复验

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中修正 `safe_command_boundary.nav2_goal_next_action`：当上次路线 action 成功但执行窗口 wheel raw L/R 仍为 0/0，且当前图上路线已 ready、执行会自动启动 runtime 时，下一步仍明确追加“并复验 wheel raw L/R”。
- 在 `pc-tools/workstation/test/catalog.test.ts` 中更新并补充断言，锁定 `nav2_goal_next_action` 与 `nav2_goal_next_action_plain` 都包含同窗口轮速复验。
- 在 `docs/product/pc_tools_workstation.md` 中记录该只读 summary 文案修正。

## 验证结果

- 已通过 Nav2 定向验证：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Nav2|nav2|wheel raw|wheel"`，结果 `32 passed | 128 skipped`。
- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `375 passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，新 PID 为 `48993`。
- 已通过 7001 只读 summary live 验证：`safe_command_boundary.nav2_goal_next_action` 包含 `并复验 wheel raw L/R`，`nav2_goal_next_action_plain` 包含 `并复验执行窗口轮速 L/R`。

## 剩余风险

- 本轮只改只读 summary 文案，不调用 Nav2 execute、不启动 runtime、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实完整 Nav2 路线闭环仍需要现场勾选安全确认后重跑，并在同窗口读到 wheel raw L/R 非零。
