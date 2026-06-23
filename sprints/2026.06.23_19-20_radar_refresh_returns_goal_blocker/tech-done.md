# 2026-06-23 19:20 Micro Sprint: 雷达刷新后回到当前目标缺口

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `刷新雷达` 在确认雷达已运行后，不再固定聚焦 `轮速记录`，改为回到 `本轮进度` 的当前第一缺口。
  - 该跳转只移动焦点，不自动试动、不执行 Nav2、不提交 delivery complete、不启用键盘、不发送 manual 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增回归测试：默认 fixture 下轮速已完成、行程待完成，点击 `刷新雷达` 后焦点回到行程前确认 checkbox，并确认没有调用 manual、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录雷达刷新后回到当前目标缺口的行为。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "returns to the current goal blocker after radar refresh confirms running"`：通过，`1 passed | 142 skipped`。
- `cd pc-tools/workstation && npm test -- -t "refreshes radar and map proof through fixed POST proxies and auto refreshes the summary|returns to the current goal blocker after radar refresh confirms running"`：通过，`2 passed | 141 skipped`。
- `cd pc-tools/workstation && npm test`：通过，`2 passed`、`143 passed`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 产物生成成功。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只提升 PC 普通首屏焦点衔接，不证明真实 `wheel raw L/R 非零`、完整 Nav2 路线执行、`delivery success` 或 PC 键盘连续手控。
- 真实上位机当前只读状态仍显示雷达未运行、Nav2 latest not_proven、delivery false，真实动作仍需现场 operator 明确确认。
