# PC free-roam map lifecycle pending

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 增加 `mapLifecyclePendingAction`，区分地图列表读取、开始记录和保存地图的 pending 状态。
- 普通首屏扫地式建图在保存地图请求未返回前明确显示 `保存中`、`正在保存当前扫图地图；保存完成前不要继续移动`，并把下一步收口为等待地图动作完成。
- 在 `pc-tools/workstation/test/App.test.ts` 扩展扫地式建图流程测试，模拟 map save POST 悬而未决，覆盖保存中 UI 与不误触 manual/Nav2/delivery 的边界。
- 更新 `docs/product/pc_tools_workstation.md` 记录地图 lifecycle pending 的普通用户语义。

## 验证结果

- 通过：`npm test -- --testNamePattern "keeps free-roam keyboard locked until map recording starts"`，1 passed / 170 skipped。
- 通过：`npm run lint`。
- 通过：`npm test`，171 passed。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 监听 `TCP *:7001`。
- 测试副作用：`npm test` 刷新两个历史 smoke artifact 的 `checked_at`；已只还原这两个时间戳，未纳入本轮改动。

## 剩余风险

- 本轮是 PC/mock 验证，不代表真实 map save 已持久化成功；真实地图保存仍以上车端返回、地图列表和现场 HIL 为准。
- 保存中状态只阻止 UI 误导，不改变后端保存接口的执行语义。
