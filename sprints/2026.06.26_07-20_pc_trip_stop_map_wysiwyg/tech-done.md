# 2026.06.26 07:20 PC trip stop map WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainTripStopRequestedDuringExecution`，只在本次图上路线执行 pending 期间记录 operator 是否点击过行程 stop。
  - 地图终点 marker、地图行程 caption、行程状态和行程进度在 stop 请求 pending 时显示 `行程停止中`，stop 转发成功后显示 `停止已发送`。
  - 新增 `stopPlainTripExecution()` 包装现有 `sendStop()`；底层仍只走 `/api/robot-control/base/stop`，不新增 Nav2 cancel。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 visible-route pending 用例，覆盖行程 stop 点击后的地图 marker、ARIA、caption、行程状态和行程进度 WYSIWYG 文案。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-26 07:20 起行程 stop 后地图和状态同步显示 stop 请求链路。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "marks the visible route goal as executing while the plain trip request is pending"`，1 passed / 191 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 files / 192 passed。
- 通过：`git diff --check`。
- 已确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true` 输出 `node ... TCP *:7001 (LISTEN)`。
- 已处理：完整 `npm test` 只改动两个 2026-06-11 旧 DOM smoke artifact 的 `checked_at`，已恢复到原始基线时间戳，未纳入提交。

## 剩余风险

- 本轮只验证 PC 端 mock/WYSIWYG 行为，不触发真实 Nav2 行程或真实底盘 stop HIL。
- 行程 stop 仍是 base stop 兜底状态，不是 Nav2 action cancel；真实 action cancel 仍需上车端接口支持。
- 本轮没有改 Clash、系统代理或上车端端口配置。
