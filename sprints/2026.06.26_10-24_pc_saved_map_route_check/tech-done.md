# PC 保存地图后自动检查图上路线

## sprint_type

micro

## 实际改动

- 普通首屏 `保存当前地图` 在保存成功且保存后的地图画面自动刷新成功后，追加一次 no-motion Nav2 proof refresh。
- proof refresh 后再次刷新地图画面，让新保存地图上的路线折线、起点和终点直接贴回普通首屏地图。
- 保存失败或保存后 preview 失败时不触发路线检查，避免把不可见/旧地图误写成路线可用。
- 更新 PC 工作站测试与产品文档，明确该自动检查不调用 `nav2/goal/execute`、manual、keyboard、delivery、stop 或 `/cmd_vel`，不修改 Clash 或系统代理，PC 入口保持 `0.0.0.0:7001`。

## 验证结果

- 通过：`npm test -- -t "keeps free-roam keyboard locked until map recording starts"`，结果为 `Test Files 1 passed | 1 skipped (2)`、`Tests 1 passed | 202 skipped (203)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果为 `Test Files 2 passed (2)`、`Tests 203 passed (203)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮验证边界是 PC 前端、mock DOM 与构建检查；未执行真实车端 HIL、真实地图保存、真实 Nav2 路线生成或真实底盘运动。
- 完整测试会刷新旧 smoke artifact 的 `checked_at` 字段；本轮已将两个旧 artifact 时间戳恢复到历史固定值，避免把无关生成噪音纳入提交。
