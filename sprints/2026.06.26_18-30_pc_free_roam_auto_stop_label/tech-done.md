# PC 自动扫图停止按钮随时可点标注

## sprint_type

micro

## 实际改动

- 自动扫图 stop 入口在可点状态下显示 `停止自动扫图（随时可点）`，让低速自动扫图运行和 start pending 时的停止兜底更明确。
- 保留 pending/排队状态：stop 请求发送中显示 `停止中`，start pending 后点击 stop 显示 `停止已排队`。
- 更新 PC 工作站回归测试，锁定 start pending 和 stop 转发返回后的 stop 按钮文案。
- 同步 `docs/product/pc_tools_workstation.md`，明确本轮只改 stop WYSIWYG 文案，不改变 stop 代理、排队逻辑或自动扫图状态机。

## 验证结果

- 通过：`npm test -- -t "queues free-roam autonomy stop while the start request is still pending"`，结果 `Test Files 1 passed | 1 skipped (2)`、`Tests 1 passed | 203 skipped (204)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`、`Tests 204 passed (204)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。

## 剩余风险

- 本轮验证边界是 PC 前端和 mock DOM；未执行真实自动扫图停止、真实底盘运动收口或 HIL。
