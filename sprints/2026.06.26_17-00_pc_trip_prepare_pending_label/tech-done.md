# PC 行程准备 Pending 文案 WYSIWYG

## sprint_type

micro

## 实际改动

- 普通首屏行程向导在 no-motion Nav2 proof refresh 未返回时，执行按钮显示 `准备路线中（不发车）`，避免用户把路线准备误解为已经发车。
- 读取最近行程结果 pending 时显示 `读取行程结果中`；只有真正 `nav2/goal/execute` pending 才显示 `执行中`。
- 更新 PC 工作站回归测试，锁定点击准备图上路线后，在 refresh 返回前不调用 `nav2/goal/execute`，按钮必须显示不发车 pending 文案。
- 同步 `docs/product/pc_tools_workstation.md`，明确本轮不修改 Clash 或系统代理配置，PC 工作站公开入口继续是 `0.0.0.0:7001`。

## 验证结果

- 通过：`npm test -- -t "refreshes the map automatically after plain trip preparation"`，结果 `Test Files 1 passed | 1 skipped (2)`、`Tests 1 passed | 203 skipped (204)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`、`Tests 204 passed (204)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。

## 剩余风险

- 本轮验证边界是 PC 前端状态和 mock DOM；未执行真实 Nav2 路线规划、真实路线执行或实车 HIL。
