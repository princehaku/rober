# Wheel zero without voltage

sprint_type: micro

## 设计

真实上位机当前 `/api/base/status` 只读链路能看到 `T=1001`，但 `L/R=0/0`，这是 `wheel raw L/R 非零` 的当前卡点。PC 首屏已有“带电压时显示排查项”的提示，但如果未来某次 summary 缺 `feedback_voltage_v`，同样的 `L/R=0/0` 不应退回成“仍需试动读到非零”这种模糊提示。

本轮只修正文案和焦点，不新增任何运动动作：

- 只要当前只读 `L/R=0/0`，`本轮进度` wheel 行就提示检查电机使能、供电、模式和现场空间。
- `去轮速` 仍只聚焦本地 `已检查轮速卡点` 按钮，不自动点击、不发 first-jog/manual。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`plainWheelGoalProgressHint` 不再依赖电压文本；只读 `L/R=0/0` 直接使用轮速卡点排查提示。
- `pc-tools/workstation/test/App.test.ts`：新增 summary 缺 `feedback_voltage_v` 且 `L/R=0/0` 的普通首屏测试，确认提示和焦点正确，且不调用 first-jog/manual。
- `docs/product/pc_tools_workstation.md`：同步记录无电压字段时的 wheel zero 提示口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "wheel zero blocker from static readback"`：通过，1 个目标用例通过，确认无电压字段但只读 `L/R=0/0` 时仍显示轮速卡点提示，`去轮速` 只聚焦本地检查按钮且不调用 first-jog/manual。
- `cd pc-tools/workstation && npm test`：通过，2 个 test files / 150 个 tests 全部通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite production build 与 server TypeScript build 完成。
- `git diff --check`：通过，无空白错误。
- 全量测试刷新了两个历史 DOM smoke artifact 的 `checked_at`；本轮已恢复为原始时间，未把旧证据时间戳变更纳入提交。

## 剩余风险

- 本轮不触发真实小车运动，不调用 radar start、first-jog、manual、keyboard pulse、stop、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `wheel raw L/R 非零` 的真实证明仍未完成：当前上位机只读状态还是 `L/R=0/0`，需要现场检查后显式低速试动采集 during-motion 非零 L/R。
