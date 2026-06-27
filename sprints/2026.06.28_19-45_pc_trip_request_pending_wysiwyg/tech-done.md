# 2026-06-28 19:45 PC 行程请求 Pending 所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏点击 `执行图上路线` 后，PC 请求尚未返回时不再显示“正在执行图上路线”。
  - 地图终点 marker、路线 caption、行程状态、进度和当前事实统一显示“行程请求已发送，等待结果返回”。
  - 保持原有 stop 兜底语义：pending 期间仍可点 `行程停止（随时可点）`，但不宣称 Nav2 action 已取消或小车已完成路线执行。
- `pc-tools/workstation/test/App.test.ts`
  - 更新延迟 execute 回包的回归测试，锁定请求 pending 窗口的 marker、aria、路线 label、当前事实和行程进度文案。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC 普通首屏 execute pending 的产品口径，避免把网络/上位机请求 pending 误说成自动驾驶已开始执行。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "request-pending"`
  - 结果：1 个测试文件通过，1 个目标测试通过，197 个测试按过滤跳过。
- 通过：`npm test`
  - 结果：2 个测试文件通过，346 个测试通过。
- 通过：`npm run lint`
  - 结果：ESLint 无报错。
- 通过：`npm run build`
  - 结果：TypeScript 与 Vite 生产构建通过；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。

## 剩余风险

- 本轮只修正 PC 普通首屏对 execute pending 窗口的显示口径，未做真实 Nav2 HIL 或上位机联调。
- 未发送任何真实 Nav2、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel` 请求。
