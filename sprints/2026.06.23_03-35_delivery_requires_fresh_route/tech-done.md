# Delivery Requires Fresh Route

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：最终送达确认新增本轮行程 gate，只有未过期的 Nav2 `goal_succeeded` 才允许 `确认送达（不发车）` 提交。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：旧行程记录下最终确认区显示 `待行程`、按钮显示 `确认送达（先重新行程）`，submit handler 直接返回，不写 operator report、不调用 delivery complete。
- `pc-tools/workstation/test/App.test.ts`：更新默认、成功提交、失败提交和 stale delivery 测试，覆盖 fresh route 才能提交，以及旧路线下全部勾选后仍禁用提交。
- `docs/product/pc_tools_workstation.md`：同步记录 delivery success 入口必须依赖本轮新鲜路线。

## 验证结果

- 通过：`npm test`，结果 `2 passed (2)`、`130 passed (130)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，结果 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只收紧 PC 端 delivery success 提交 gate，没有真实执行 Nav2 或送达确认。
- 真实上位机仍需现场重新完成本轮 Nav2 行程、wheel raw L/R 非零、delivery success 和键盘连续手控验证。
