# Nav2 Latest Age Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：Nav2 goal execute/latest 的短摘要新增 `generated_at_ms`、`response_generated_at_ms`、`completed_at_ms`；delivery 摘要新增 `nav2_generated_at_ms`，用于前端判断最近路线材料新旧。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `行程执行` 与 `任务收口` 在读到时间字段时显示“约 N 分钟/小时/天前”；超过 15 分钟的 latest 成功额外提示需要本轮复验。
- `pc-tools/workstation/test/App.test.ts`：新增 stale latest Nav2 success DOM 测试，确认普通首屏展示旧证据年龄，且不调用 Nav2 execute、delivery complete、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录普通首屏 Nav2 latest 年龄提示边界。

## 验证结果

- 通过：`npm test`，结果 `2 passed (2)`、`130 passed (130)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，结果 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 PC 页面如何呈现最新 Nav2 成功材料的新旧程度，不执行真实 Nav2 路线。
- 真实上位机当前 delivery success、wheel raw L/R 非零和键盘连续手控仍需现场操作材料完成；本 sprint 不宣称这些目标已闭环。
