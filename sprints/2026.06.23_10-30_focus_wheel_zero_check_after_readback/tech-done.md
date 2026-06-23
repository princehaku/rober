# 只读轮速 0/0 后聚焦排查

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`刷新当前轮速（只读）` 或高级 `采集底盘反馈` 读到 T1001 但 L/R 仍为 `0/0` 时，自动把焦点移到 `已检查轮速卡点` 本地按钮。该动作只改变焦点，不自动点击排查按钮，不发送 first-jog/manual/stop/Nav2/delivery 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：扩展 L/R=`0/0` 只读采样测试，验证焦点落到 `plain-wheel-zero-check`，并确认没有调用 first-jog 或 manual。
- `docs/product/pc_tools_workstation.md`：同步只读轮速 0/0 后的本地排查引导规则。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、137 个用例通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，完成 app/server TypeScript 与 Vite production build。
- 通过：`git diff --check`。
- 已恢复 `npm test` 改写的历史 smoke JSON `checked_at` 副作用，提交范围不包含旧 artifacts 噪声。

## 剩余风险

- 本轮只改善 PC 对当前 `L/R=0/0` 卡点的现场引导，不证明 wheel raw L/R 非零。
- 真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 和真实 PC 键盘连续手控仍需要现场操作和证据。
