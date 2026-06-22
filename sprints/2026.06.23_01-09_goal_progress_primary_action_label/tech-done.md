# 2026-06-23 01:09 去处理卡点动态文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 主按钮从泛化 `去处理卡点` 改成动态文案。
- 当前第一缺口是行程时显示 `去行程卡点`，轮速时显示 `去轮速记录卡点`，送达时显示 `去送达卡点`，键盘时显示 `去键盘手控卡点`。
- 按钮行为不变，只滚动并聚焦页面内面板，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：补充默认行程卡点、L/R=0/0 轮速卡点、行程成功后送达卡点三类按钮文案断言。
- `docs/product/pc_tools_workstation.md`：同步记录该动态文案。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 首屏卡点按钮可读性；不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或 PC 键盘连续手控。
- 真实能力仍需要现场 operator 按安全口径显式执行并提供实车证据。
