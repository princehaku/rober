# PC 最近路线重新准备按钮不发车标注

## sprint_type

micro

## 实际改动

- 普通首屏地图只显示 `最近路线` 时，行程向导按钮从 `重新准备路线` 改为 `重新准备路线（不发车）`。
- 更新 PC 工作站测试，锁定最近路线状态下按钮文案必须带不发车标注，点击仍不会调用 `nav2/goal/execute`、manual 或 `/cmd_vel`。
- 同步 `docs/product/pc_tools_workstation.md`，明确旧路线只能读图参考，重新准备仍是 no-motion 路线刷新。

## 验证结果

- 通过：`npm test -- -t "marks stale path preview points as a recent route instead of an executable route"`，结果 `Test Files 1 passed | 1 skipped (2)`、`Tests 1 passed | 203 skipped (204)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`、`Tests 204 passed (204)`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 进程监听 `TCP *:7001 (LISTEN)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。

## 剩余风险

- 本轮只改善 PC 普通首屏文案与测试，不执行真实 Nav2 重新规划、真实路线执行或实车 HIL。
