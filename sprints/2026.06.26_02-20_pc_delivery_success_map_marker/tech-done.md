# PC 地图送达成功 Marker

sprint_type: micro

## 目标

让普通首屏地图不只显示 Nav2 目标“已到达”，还要在本轮 delivery gate 已经确认且 route/map ref 对齐当前 Nav2 执行证据时，直接在地图目标点显示“已送达”。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图 Nav2 目标 marker 复用既有 `deliverySuccessReady` gate。
  - 只有本轮 Nav2 goal_succeeded 带反馈样本且 delivery success 未过期、route/map ref 对齐时，目标 marker 才从 `已到达` 提升为 `已送达`。
  - aria 文案同步说明 delivery gate 已确认。
- `pc-tools/workstation/src/styles.css`
  - 为 `已送达` 目标 marker 增加绿色成功态样式。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 delivery success 对齐本轮 Nav2 evidence 的地图 marker 单测。
  - 同时断言该只读显示不触发 Nav2 execute、delivery complete 或 manual。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏地图送达成功 marker 的 WYSIWYG 边界。

## 验证结果

- `npm test -- -t "marks the map goal as delivered"`：通过，1 个定向用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 生产构建完成。
- `npm test`：通过，2 个测试文件、177 个用例全部通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 `node` 正在监听 `TCP *:7001`。

## 剩余风险

- 本轮是 PC 端 mock/单元验证；只证明 UI 会正确消费已读回的 delivery success，不等价于真车完成投放或现场 HIL。
