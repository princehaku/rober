# 2026-06-22 18:05 Keyboard Contract Plain Gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：把 PC 键盘连续手控的可用条件统一为“后端 summary 声明 `bounded_repeating_manual_pulse` 合同 + manual gate 已满足”。普通首屏本轮进度、键盘面板、`启用键盘` 按钮、目标收口 checklist 和高级诊断现在使用同一口径。
- `pc-tools/workstation/test/App.test.ts`：更新默认缺口文案，并新增“现场材料已齐但 summary 缺键盘合同仍禁用键盘”的回归测试，确认不会发送 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`：同步记录 summary 键盘合同缺失时的 UI 和安全边界。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只修 PC 前端 gate 一致性，未执行真实键盘长按上车 smoke；真实运动仍需现场 operator 明确确认后再验证。
- 当前真实上位机 delivery success 仍缺最终人工确认材料，wheel raw L/R 真实读回仍是 `0/0`；本轮没有把这些证据外推为完成。
