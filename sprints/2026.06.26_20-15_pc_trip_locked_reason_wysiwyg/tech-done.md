# PC 图上路线 Nav2 locked 原因所见即所得

## sprint_type

micro

## 背景

- live 7001 summary 显示 `nav2_goal=Nav2 NavigateToPose locked`，这类上车端拒绝原因如果只显示为“执行失败”，普通用户难以判断下一步。
- 本轮不扩大预检，不改变发车 gate，只把后端 locked/not ready 执行拒绝翻译成普通用户可读的 WYSIWYG 状态。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plainTripFailureReasonText` 新增 `locked/not_ready/not ready/unavailable` 映射，统一显示为 `行程未开放`。
  - 地图终点 marker、`行程执行` caption、行程状态和进度继续复用同一短原因。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `shows locked Nav2 execution as trip not open on the visible route`，覆盖路线可见、安全确认已勾、后端返回 `Nav2 NavigateToPose locked` 的场景。
  - 断言普通首屏不暴露 `NavigateToPose locked`，也不调用 delivery、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 `行程未开放` 的展示口径和安全边界。

## 验证结果

- `npm test -- -t "locked Nav2|trip execution fails|failed plain trip"`：通过，1 个 test file，3 passed，206 skipped。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 保留既有 `Some chunks are larger than 500 kB` warning。
- `npm test`：通过，2 个 test file，209 passed。
- 全量测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，已用精确 patch 恢复，避免把测试副作用纳入本轮提交。

## 剩余风险

- 本轮是 PC 端文案/状态映射和 mock 单元验证，未做真实 Nav2 上车执行 HIL。
- `行程未开放` 只是把后端 locked/not ready 拒绝变成普通用户可读状态，不改变上车端是否允许 NavigateToPose。
