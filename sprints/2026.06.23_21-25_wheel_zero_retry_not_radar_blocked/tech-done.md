# 2026-06-23 21:25 Micro Sprint: 轮速 0/0 重试不再被雷达缺口覆盖

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏读到 wheel L/R=`0/0` 时，`wheel raw L/R 非零` 的下一步保持在轮速本身：先 `已检查轮速卡点`，再 `检查后重试读非零 L/R`。
  - `检查后重试读非零 L/R` 不再因为雷达 lifecycle 未运行而被替换成 `先启动雷达再试动`。
  - 轮速重试仍要求 first-jog gate 和现场材料满足，且本地 `已检查轮速卡点` 已点击；页面不会自动调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 wheel L/R=`0/0` 回归测试，锁定主进度按钮、wheel 行按钮、焦点和重试按钮的新口径。
  - 保持“未点击卡点检查不会自动发车”的断言；点击重试按钮才调用固定 first-jog proxy。
- `docs/product/pc_tools_workstation.md`
  - 同步当前规则，并明确 2026-06-23 14:45 / 15:00 的“先去雷达”旧口径已被替换。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "shows current wheel L/R and frame count in plain goal progress from summary"`：通过，`1 passed | 143 skipped`。
- `cd pc-tools/workstation && npm test -- -t "explains plain first-jog wheel retry when motion frames keep L/R at zero"`：通过，`1 passed | 143 skipped`。
- `cd pc-tools/workstation && npm test`：通过，`2 passed`、`144 passed`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 产物生成成功。
- `git diff --check`：通过。

## 剩余风险

- 本轮只改 PC 端 wheel L/R=`0/0` 的下一步和焦点，不证明真实 `wheel raw L/R 非零` 已完成。
- 2026-06-23 真实只读状态仍显示：上位机 `8787` 在线，T1001 可读但 L/R 为 `0/0`，雷达 lifecycle 未运行，delivery success 为 `false`。真实试动仍需现场 operator 明确点击并满足 first-jog gate。
