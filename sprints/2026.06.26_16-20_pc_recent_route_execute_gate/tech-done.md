# PC 最近路线执行 gate WYSIWYG

## sprint_type

micro

## 实际改动

- 普通首屏地图只显示 `最近路线` 时，安全确认已勾选后执行按钮显示 `先重新准备路线` 并保持禁用。
- 路线说明同步保留“地图上显示的是最近路线；先准备行程，再执行新的图上路线”，避免旧 path preview 被误当成当前可执行路线。
- 更新 PC 工作站测试，锁定最近路线状态下点击执行按钮不会调用 `nav2/goal/execute`、manual 或 `/cmd_vel`。
- 同步 `docs/product/pc_tools_workstation.md`，明确该 gate 不自动重新规划、不执行 Nav2、不发送手控/stop/delivery，不修改 Clash/系统代理，PC 入口保持 `0.0.0.0:7001`。

## 验证结果

- 通过：`npm test -- -t "marks stale path preview points as a recent route instead of an executable route"`，结果 `Test Files 1 passed | 1 skipped (2)`，`Tests 1 passed | 201 skipped (202)`。
- 通过：`npm run lint`。
- 通过：`npm run build`。Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提醒，不影响本轮功能。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`，`Tests 202 passed (202)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端 gate 和 mock/单测验证，未做真实 Nav2 重新规划或实车路线执行验证。
