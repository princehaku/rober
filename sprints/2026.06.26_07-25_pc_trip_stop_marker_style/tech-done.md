# 2026.06.26 07:25 PC trip stop marker style

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`
  - 为地图终点 marker 的 `data-state="停止中"` 增加警示色样式。
  - 为 `data-state="停止已发送"` 增加蓝色收口样式，避免行程 stop 状态落回默认目标样式。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展行程执行 pending 测试，读取 `src/styles.css` 并断言两个 stop marker 状态选择器存在。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-26 07:25 起行程 stop marker 独立样式口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "marks the visible route goal as executing while the plain trip request is pending"`，1 passed / 191 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 files / 192 passed。
- 通过：`git diff --check`。
- 已确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true` 输出 `node ... TCP *:7001 (LISTEN)`。
- 已处理：完整 `npm test` 只改动两个 2026-06-11 旧 DOM smoke artifact 的 `checked_at`，已恢复到原始基线时间戳，未纳入提交。

## 剩余风险

- 本轮只验证 PC 端 CSS/DOM 口径，不触发真实 Nav2 行程或真实底盘 stop HIL。
- 行程 stop 样式仍只表达 base stop 兜底状态，不代表 Nav2 action cancel 已接入。
- 本轮没有改 Clash、系统代理或上车端端口配置。
