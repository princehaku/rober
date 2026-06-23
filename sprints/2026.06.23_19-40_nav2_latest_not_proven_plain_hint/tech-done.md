# 2026-06-23 19:40 Micro Sprint: Nav2 latest 未证明时普通提示不装作未读取

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainTripLatestNotProvenEvidence`，当 `GET /api/robot-control/nav2/goal/execution/latest` 已加载但最近行程不是 `goal_succeeded` 时，普通首屏提示 `最近行程未通过，需要检查或重新执行完整行程`。
  - 行程卡、`本轮进度`、验收卡点、送达下一步和高级 `目标收口进度` 的 Nav2 项统一使用该提示。
  - 普通首屏仍不暴露 `not_proven` 字段名，不自动执行 Nav2、delivery complete、manual、keyboard pulse 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 latest `not_proven` 回归测试，确认普通首屏显示未通过提示，同时没有调用 Nav2 execute、delivery complete、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 Nav2 latest 未证明时的普通提示规则。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "shows latest Nav2 not-proven as a checked but incomplete trip result"`：通过，`1 passed | 143 skipped`。
- `cd pc-tools/workstation && npm test`：通过，`2 passed`、`144 passed`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 产物生成成功。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只改善 PC 普通首屏对 latest `not_proven` 的解释，不证明真实 `wheel raw L/R 非零`、完整 Nav2 路线执行、`delivery success` 或 PC 键盘连续手控。
- 真实上位机当前只读状态仍显示雷达未运行、Nav2 latest `not_proven`、delivery false；真实动作仍需现场 operator 明确确认。
