# Keyboard Restore First-Jog Hint

## sprint_type

micro

## 目标

- 继续推进 PC 端易用性和 `PC 键盘连续手控` 的前置闭环。
- 当送达草稿覆盖 first-jog 基础确认时，键盘区也应指向“恢复试动确认”，避免现场按键盘流程重复做泛化检查。
- 不调用 subagent；不发送真实运动、Nav2 执行、delivery complete 或 keyboard/manual pulse。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `firstJogMaterialRestoreBlocksMotion` 统一判断。
  - 键盘缺项、启用按钮、复查按钮和下一步提示在该状态下优先显示“恢复试动确认”。
  - 保持键盘启用和 pulse gate 不变，不绕过 manual/operator material 检查。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 restore-first-jog 场景测试，锁定键盘区按钮文案和下一步提示。
  - 继续断言不会调用 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-23 06:05 起的键盘区恢复确认引导。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 135 passed (135)`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- 通过：`git diff --check`

## 剩余风险

- 本轮只改善 PC 首屏引导，不证明真实车已完成 wheel raw L/R 非零、完整 Nav2 路线执行、送达成功或键盘连续手控。
- 真实上车仍需 operator 显式点击恢复试动确认并在安全现场低速试动，当前不会由 PC 自动执行。
