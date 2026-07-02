# 2026.07.02 22:25 雷达贴图刷新安全边界

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为雷达贴图只读刷新补齐完整安全边界字段，覆盖 Nav2、manual、keyboard、free-roam、map runtime、delivery 和 stop。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：在 `live_closure_summary` 和 summary 顶层输出同源 `radar_overlay_refresh_*` 边界。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：在 `plain-live-closure-summary` 和 `plain-live-closure-wysiwyg-diagnostics` DOM 暴露同组边界，便于现场 smoke 直接验收。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：新增 summary 与 DOM 断言，防止雷达贴图刷新被误接到运动或运行时入口。
- `docs/product/pc_tools_workstation.md`：同步记录雷达贴图刷新只读边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed / 247 passed`。
- `git diff --check`：通过，无 whitespace error。
- `cd pc-tools/workstation && npm run build`：通过，Vite 仍提示既有 chunk size warning。
- `cd pc-tools/workstation && npm run lint`：通过。

## 剩余风险

- 本轮只覆盖 PC/API/DOM 合同和 mock 测试；真实车上雷达刷新后的贴图效果仍需要现场访问 `http://<PC>:7001/map` 或 summary endpoint 复核。
