# Tech Done

- sprint_type: micro
- 目标：收紧 PC 键盘连续手控验证，确保“连续”来自同一次按住会话，而不是跨松开的单脉冲累计。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `keyboardHoldPulseCount`，区分当前按住会话脉冲数和历史最佳连续脉冲数。
  - 只有同一次按住内连续成功转发至少 2 个 bounded manual pulse，`PC 键盘连续手控` 才标记为已验证。
  - 松开、失败或停止会清空当前按住计数；历史最佳只用于提示，不直接把分散脉冲累加成验证。
  - 普通首屏文案改为 `本次按住 ...`、`最佳连续 ...` 和 `已连续 2/2 次`，现场能看懂还差哪一步。
- `pc-tools/workstation/test/App.test.ts`
  - 更新键盘连续手控回归测试，覆盖第一次单脉冲松开不验证、第二次按住第一脉冲仍不验证、同次按住第二脉冲后才验证。
- `docs/product/pc_tools_workstation.md`
  - 同步记录键盘连续手控不再跨松开累计脉冲。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，2 个 test files、133 个 tests passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc` 完成。
- `git diff --check`：通过。

## 剩余风险

- 本轮只验证 PC 前端键盘状态机和 fixed proxy 调用合同；不包含真实硬件连续手控 HIL、真实地面运动或现场安全验收。
