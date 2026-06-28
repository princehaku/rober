# 2026.06.29 11:10 PC free-roam next action frontend

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏自由移动下一步优先消费 `safe_command_boundary.free_roam_autonomy_next_action`，让 UI 直接显示“可先自由移动；建图验收还差 ...”。
- `pc-tools/workstation/test/App.test.ts`：更新普通首屏断言，并覆盖仅缺地图记录时的 summary next action。
- `docs/product/pc_tools_workstation.md`：同步记录前端消费新字段和只读安全边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts -t "plain user|mapping-ready|mapping ready|free roam"`，结果 `1 passed`、`3 passed | 209 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`366 passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 和 `vite build` 成功；Vite 仅保留既有大 chunk warning。
- 通过：`git diff --check -- pc-tools/workstation/src/components/RobotControlConsolePanel.vue pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md sprints/2026.06.29_11-10_pc_free_roam_next_action_frontend/tech-done.md`，无 whitespace 问题。
- 通过：App DOM 测试覆盖普通首屏 `plain-free-roam-autonomy-next-action` 消费 summary next action；ready fixture 显示 `自动扫图下一步：已进入自动扫图条件；继续低速监看地图、雷达和画面。`，locked fixture 仍按本地按钮状态兜底，避免旧 summary 占位文案覆盖可点击入口。

## 剩余风险

- 本轮只把 summary 的自由移动下一步接到 PC 普通首屏，不执行自由移动、不启动地图记录、不证明真实建图。
- 未获得本轮现场安全确认，因此不执行 Nav2 goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
