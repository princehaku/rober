# 2026.06.26 07:15 PC trip inline stop

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏执行图上路线 `navGoalExecutionPending` 时，在 `行程操作` 区就地显示红色 `行程停止（随时可点）`。
  - 按钮复用现有 `sendStop()` / `/api/robot-control/base/stop` 兜底路径；stop pending 时显示 `停止中`，不新增 Nav2 cancel、manual/keyboard pulse、delivery 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展执行 pending 的图上路线测试：验证行程区 stop 按钮出现、可点击、pending 文案和禁用态正确，且只调用 `/api/robot-control/base/stop`。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-26 07:15 起行程执行期间的就近 stop 兜底行为。

## 验证结果

- 未匹配：`cd pc-tools/workstation && npm test -- -t "shows a map-level pending state while visible-route trip execution is in flight"`，Vitest 输出 192 skipped；已改用准确用例名重跑。
- 通过：`cd pc-tools/workstation && npm test -- -t "marks the visible route goal as executing while the plain trip request is pending"`，1 passed / 191 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 files / 192 passed。
- 通过：`git diff --check`。
- 已确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true` 输出 `node ... TCP *:7001 (LISTEN)`。
- 已处理：完整 `npm test` 只改动两个 2026-06-11 旧 DOM smoke artifact 的 `checked_at`，已恢复到原始基线时间戳，未纳入提交。

## 剩余风险

- 本轮只验证 PC 端 mock 行为，不触发真实 Nav2 行程或真实底盘 stop HIL。
- 行程 stop 仍是现有 base stop 兜底，不是 Nav2 action cancel；真实 Nav2 action cancel 能力仍依赖上车端后续接口。
- 本轮没有改 Clash、系统代理或上车端端口配置。
