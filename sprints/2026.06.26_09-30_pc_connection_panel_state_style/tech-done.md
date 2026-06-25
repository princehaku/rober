# 2026-06-26 09:30 PC 连接卡片外层状态线

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“小车连接”卡片新增 `data-testid="plain-connection-panel"` 和 `data-state=robotConnectionSummary.state`。
  - 状态来源沿用已有连接摘要，不新增刷新、控制或真实机器人调用。
- `pc-tools/workstation/src/styles.css`
  - 为 `.plain-connection-panel` 增加外层状态线：`已连接` 成功态、`未连接` 中性态、`有异常` 异常态。
- `pc-tools/workstation/test/App.test.ts`
  - 默认首屏断言连接卡片存在且 `data-state="已连接"`。
  - 全 timeout 场景断言连接卡片 `data-state="有异常"`。
  - 锁定连接卡片状态样式选择器存在。
- `docs/product/pc_tools_workstation.md`
  - 补充普通首屏“小车连接”外层状态线的产品口径和控制边界。

## 验证结果

- `npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|shows a plain timeout hint when the robot API does not respond"`：通过，`1 passed | 1 skipped (2)`，`2 passed | 190 skipped (192)`。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `npm test`：通过，`2 passed (2)`，`192 passed (192)`。
- `git diff --check`：通过，无空白错误。
- 全量测试会刷新 2026-06-11 两个旧 DOM smoke artifact 的 `checked_at`；本轮已恢复为基线时间戳，避免无关产物进入提交。

## 剩余风险

- 本轮只做 PC 前端 mock/静态验证，不触发真实小车运动，也不证明 HIL。
- Node 当前应继续监听 `0.0.0.0:7001`；本轮不修改 Clash、代理或系统网络配置。
