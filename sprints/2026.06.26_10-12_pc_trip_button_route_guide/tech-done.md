# PC 行程按钮路线向导

## sprint_type

micro

## 实际改动

- `行程操作` 的主按钮从“无图上路线时禁用”改为路线向导：勾选安全确认后，没有当前图上路线时显示 `准备图上路线` / `刷新图上路线` 并可点击。
- 点击上述向导状态只触发 no-motion Nav2 proof refresh 和只读地图画面刷新；本次点击不会继续调用 `nav2/goal/execute`。
- 只有当前路线已经真实画到地图上后，按钮才显示 `执行图上路线`，再次点击才走既有固定 execute 代理。
- 更新 PC 工作站测试与产品文档，明确该行为不自动发车、不发送 manual/keyboard/delivery/stop 或 `/cmd_vel`，不修改 Clash 或系统代理，PC 入口保持 `0.0.0.0:7001`。

## 验证结果

- 通过：`npm test -- -t "plain trip"`，结果为 `Test Files 1 passed | 1 skipped (2)`、`Tests 7 passed | 195 skipped (202)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果为 `Test Files 2 passed (2)`、`Tests 202 passed (202)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮验证边界是 PC 前端、mock DOM 与构建检查；未执行真实车端 HIL、真实 Nav2 行程执行、真实雷达或底盘运动。
- 完整测试会刷新旧 smoke artifact 的 `checked_at` 字段；本轮已将两个旧 artifact 时间戳恢复到历史固定值，避免把无关生成噪音纳入提交。
