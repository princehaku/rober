# Delivery Draft Age Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：delivery latest/check/complete 的短摘要新增 `response_generated_at_ms`，让前端可以用上位机响应时间计算草稿新旧。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `任务收口` 的送达材料草稿状态在读到时间字段时显示“约 N 分钟/小时/天前”；超过 15 分钟时提示本轮重新到达需要重新准备材料或重新确认。
- `pc-tools/workstation/test/App.test.ts`：扩展 latest delivery 草稿恢复测试，验证旧草稿年龄提示，并继续断言不调用 operator report、delivery complete、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录送达草稿年龄提示和只读边界。

## 验证结果

- 通过：`npm test`，结果 `2 passed (2)`、`130 passed (130)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，结果 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改善 PC 普通首屏对旧送达草稿的解释，不替 operator 做最终确认，不产生 delivery success。
- 真实上位机当前仍需要现场重新完成 wheel raw L/R 非零、最终送达确认和键盘连续手控材料。
