# 2026-06-23 05:20 nav2 direct result blocks delivery

sprint_type: micro

## 实际改动

- 收紧 PC 前端 Nav2 证据优先级：一旦页面已读到本页执行结果或直接 `nav2/goal/execution/latest`，就用该直接结果作为本轮行程权威来源，不再让 `delivery/latest` 的旧摘要补全行程完成状态。
- 修正 no-feedback Nav2 success 回归测试：直接 latest 返回 `goal_succeeded` 但 `feedback_sample_count=0` 时，即使送达材料和人工确认项都已勾选，最终确认仍显示 `确认送达（先重新行程）` 并保持禁用。
- 测试确认该场景不调用 `POST /api/robot-control/operator/report`、`POST /api/robot-control/delivery/complete`、Nav2 execute、manual 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md`，记录直接 Nav2 latest 优先于 delivery latest 摘要的收口口径。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test`，`Test Files 2 passed (2)`，`Tests 134 passed (134)`。第一轮测试暴露断言放错用例，已修正后重新通过。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`，Vite client build 和 server TypeScript build 均完成。
- 已通过：`git diff --check`。
- 测试期间两个历史 DOM smoke JSON 只改动 `checked_at`，已还原为原始时间戳，未纳入本轮 diff。

## 剩余风险

- 本轮只修正 PC 前端收口 gate 和测试，不包含真实上位机完整 Nav2 路线执行、delivery success 或键盘连续手控 HIL 验证。
