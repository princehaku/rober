# 2026-06-23 20:20 Micro Sprint: 送达检查同步 Nav2 未通过提示

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 高级 `送达收口检查` 的 `Nav2 路线执行成功` 子项复用 latest 未通过口径。
  - 读到最近行程不是成功时，提示 `最近行程未通过，需检查或重新执行完整行程`，不再笼统提示“先读取或执行最近 Nav2 目标”。
  - 只调整只读提示，不自动执行 Nav2、delivery complete、manual、keyboard pulse 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 latest `not_proven` 回归测试，确认高级送达 checklist 的 Nav2 子项也显示未通过提示。
- `docs/product/pc_tools_workstation.md`
  - 同步记录高级送达检查对 latest 未通过提示的口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "shows latest Nav2 not-proven as a checked but incomplete trip result"`：通过，`1 passed | 143 skipped`。
- `cd pc-tools/workstation && npm test`：通过，`2 passed`、`144 passed`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 产物生成成功。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只对齐 PC 送达检查提示，不证明真实 `wheel raw L/R 非零`、完整 Nav2 路线执行、`delivery success` 或 PC 键盘连续手控。
- 真实上位机当前仍是雷达未运行、Nav2 latest `not_proven`、delivery false；真实动作仍需现场 operator 明确确认。
