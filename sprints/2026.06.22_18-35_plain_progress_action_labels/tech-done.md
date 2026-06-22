# 2026-06-22 18:35 Plain Progress Action Labels

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 四个快捷按钮从统一“去处理”改为 `去轮速 / 去行程 / 去送达 / 去键盘`，让现场人员直接知道按钮会跳到哪个面板。
- `pc-tools/workstation/test/App.test.ts`：更新首屏断言，并锁住四个快捷按钮仍只做页面 focus，不调用 Nav2 execution、delivery complete、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录该变化只是普通首屏导航，不触发任何机器人 API。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只提升 PC 首屏易用性，不产生 wheel raw L/R 非零、delivery success 或真实键盘长按 HIL 证据。
- 当前真实上位机只读复查仍显示 Nav2 goal succeeded，但 delivery success 未确认，底盘 T1001 的 L/R 仍为 0/0。
