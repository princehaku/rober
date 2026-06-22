# 2026-06-23 01:06 本轮进度去处理卡点

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 标题行新增 `去处理卡点` 按钮。
- 该按钮自动指向当前第一项未完成目标，并复用既有本地聚焦逻辑：轮速记录、行程操作、送达确认或键盘手控。
- 按钮只滚动并聚焦页面内面板，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：补充默认状态下主按钮聚焦当前行程卡点且不触发任何机器人 API。
- `docs/product/pc_tools_workstation.md`：同步记录该只读导航按钮。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 首屏卡点定位效率；不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或 PC 键盘连续手控。
- 真实能力仍需要现场 operator 按安全口径显式执行并提供实车证据。
