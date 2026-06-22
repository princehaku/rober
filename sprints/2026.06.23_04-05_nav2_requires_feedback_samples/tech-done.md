# Tech Done

- sprint_type: micro
- 目标：收紧 PC 端“完整 Nav2 路线执行”判定，避免只有 `goal_succeeded` 但没有执行反馈样本的摘要被当作本轮完整路线。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 Nav2 反馈样本计数解析，完整行程 gate 改为 `goal_succeeded` + `feedback_sample_count/nav2_feedback_sample_count > 0` + 未过期。
  - 新鲜 success 但缺反馈样本时，普通首屏显示“最近行程缺少反馈样本，需要重新读取或执行完整行程”，并阻止送达最终确认。
  - delivery route/material ref 匹配逻辑也只引用完整行程，防止无反馈样本的 success 进入送达材料链路。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 fresh Nav2 success 但 `feedback_sample_count=0` 的回归测试，覆盖行程未完成、送达确认禁用、不提交 operator report/delivery complete。
  - 给原本表示完整路线的 delivery gap fixture 补齐反馈样本计数。
- `docs/product/pc_tools_workstation.md`
  - 同步记录完整 Nav2 路线执行必须带反馈样本，且该规则不自动发车、不确认送达。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，2 个 test files、132 个 tests passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc` 完成。
- `git diff --check`：通过。

## 剩余风险

- 本轮只验证 PC 前端和 fixture 合同；不包含真实 Nav2 运行、真实反馈采样链路或真实 delivery success HIL。
