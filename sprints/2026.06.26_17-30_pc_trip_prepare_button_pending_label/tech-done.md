# PC 准备行程按钮 Pending 不发车标注

## sprint_type

micro

## 实际改动

- 普通首屏单独的 `准备行程（不发车）` 按钮在 no-motion Nav2 proof refresh pending 时显示 `准备中（不发车）`，不再只显示泛化 `准备中`。
- 更新 PC 工作站回归测试，锁定点击行程向导准备路线后，准备按钮和执行向导按钮都必须带不发车 pending 文案，并且不调用 `nav2/goal/execute`。
- 同步 `docs/product/pc_tools_workstation.md`，明确该 pending 只表示路线刷新未返回，不代表发车。

## 验证结果

- 通过：`npm test -- -t "refreshes the map automatically after plain trip preparation"`，结果 `Test Files 1 passed | 1 skipped (2)`、`Tests 1 passed | 203 skipped (204)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`、`Tests 204 passed (204)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。

## 剩余风险

- 本轮只覆盖 PC 前端 pending 文案与 mock DOM；未执行真实 Nav2 规划、真实路线执行或实车 HIL。
