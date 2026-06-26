# PC 自动扫图雷达 blocker 状态同步

## sprint_type

micro

## 实际改动

- 普通首屏 `自动扫图准备` 的雷达 blocker 复用雷达卡片真实状态，例如 lifecycle running 但 proof stale 时显示 `雷达待刷新`，不再泛化为 `雷达未保持运行`。
- 更新 PC 工作站测试，锁定上述状态：自动扫图准备面板必须显示 `雷达待刷新`，且不得再显示 `雷达未保持运行`。
- 同步 `docs/product/pc_tools_workstation.md`，明确该提示只改 WYSIWYG 文案，不自动启动/刷新雷达，不发送控制命令，不修改 Clash/系统代理，PC 入口保持 `0.0.0.0:7001`。

## 验证结果

- 通过：`npm test -- -t "keeps trip controls safety-gated while running lidar proof only asks for refresh"`，结果为 `Test Files 1 passed | 1 skipped (2)`、`Tests 1 passed | 201 skipped (202)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果为 `Test Files 2 passed (2)`、`Tests 202 passed (202)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮验证边界是 PC 前端、mock DOM 与构建检查；未执行真实车端 HIL、真实雷达刷新、真实 Nav2 自主扫图或底盘运动验证。
- 完整测试会刷新旧 smoke artifact 的 `checked_at` 字段；本轮已将两个旧 artifact 时间戳恢复到历史固定值，避免把无关生成噪音纳入提交。
