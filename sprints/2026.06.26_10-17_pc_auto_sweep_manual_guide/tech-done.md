# PC 自动扫图未就绪时的人工扫图向导

## sprint_type

micro

## 实际改动

- `自动扫图准备` 未 ready 时，`按步骤人工扫图` 不再只聚焦下一步；在已勾安全确认后会推进人工扫图的非运动步骤。
- 还没启动地图记录时，点击只调用固定 `/api/robot-control/map/start`，并在地图记录成功后启用键盘窗口等待按住。
- 地图记录已启动但键盘未启用时，点击只启用键盘窗口；真正移动仍必须 operator 按住方向键、W/A/S/D 或屏幕方向键。
- 更新 PC 工作站测试与产品文档，明确该向导不调用自动扫图 start、不发送 manual pulse、不执行 Nav2/delivery/stop 或 `/cmd_vel`，不修改 Clash 或系统代理，PC 入口保持 `0.0.0.0:7001`。

## 验证结果

- 通过：`npm test -- -t "free-roam|auto-sweep|sweep"`，结果为 `Test Files 2 passed (2)`、`Tests 15 passed | 188 skipped (203)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果为 `Test Files 2 passed (2)`、`Tests 203 passed (203)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮验证边界是 PC 前端、mock DOM 与构建检查；未执行真实车端 HIL、真实自动扫图、真实键盘运动或真实地图保存验收。
- 完整测试会刷新旧 smoke artifact 的 `checked_at` 字段；本轮已将两个旧 artifact 时间戳恢复到历史固定值，避免把无关生成噪音纳入提交。
