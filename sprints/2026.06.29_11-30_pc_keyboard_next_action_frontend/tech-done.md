# 2026.06.29 11:30 PC keyboard next action frontend

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏键盘下一步在连接、键盘合同和行程状态通过后，优先消费 summary 的 `keyboard_control_next_action`；已可手控且需要 wheel raw L/R 复验时仍保留本地更具体的轮速提示。
- `pc-tools/workstation/test/App.test.ts`：更新普通首屏键盘下一步断言，确认未勾安全确认时也显示后端完整连续手控口径。
- `docs/product/pc_tools_workstation.md`：同步记录前端消费字段和只读安全边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts -t "plain user|keyboard"`，结果 `1 passed`、`21 passed | 191 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`366 passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 和 `vite build` 成功；Vite 仅保留既有大 chunk warning。
- 通过：App DOM 测试覆盖 `plain-keyboard-next-action` 与 `plain-goal-progress-next-keyboard` 消费 summary 的完整连续手控口径：`勾选现场安全确认后点击启用键盘；按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页会停。`
- 待执行：`git diff --check`

## 剩余风险

- 本轮只改 PC 普通首屏键盘下一步文案，不启用键盘、不发送方向 pulse、不证明真实连续手控。
- 未获得本轮现场安全确认，因此不执行 Nav2 goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
