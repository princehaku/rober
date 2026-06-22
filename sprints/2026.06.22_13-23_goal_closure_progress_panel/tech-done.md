# Goal Closure Progress Panel

sprint_type: micro

## 实际改动

- PC 高级诊断顶部新增 `目标收口进度`，集中展示本轮长期目标的四个状态：`wheel raw L/R 非零`、`完整 Nav2 路线执行`、`delivery success`、`PC 键盘连续手控`。
- 面板只读当前已加载的 summary、Nav2 latest、delivery latest/check/complete、first-jog 和 base feedback sample 结果，不自动发车、不提交 operator report、不调用 delivery complete。
- 普通首屏继续保持简易风格，不显示目标进度或工程词。
- 补充 Vue 测试，覆盖普通首屏不出现 `目标收口进度`，高级诊断能看到四个目标项且不出现 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md` 记录目标进度面板边界。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`112 passed (112)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`。

## 当前真实证据

- 当前 PC summary 可读但 `console_status=blocked`，原因包含 radar latest 404。
- 当前 operator report 是 delivery draft，`wheel_feedback=false`、`lidar_delta=false`、`delivery_claim=false`。
- 当前 base feedback samples latest 的 L/R 仍为 `0/0`，`wheel_feedback_lr_nonzero_proven=false`。
- Nav2 route execution 历史 latest 仍有 `goal_succeeded` 证据，但 delivery gate 未通过。

## 剩余风险

- 本轮是可视化收口进度，不执行真实 wheel/manual/Nav2/delivery 动作。
- 真正完成仍需要现场产生 wheel raw L/R 非零、保留/复核 Nav2 goal_succeeded、完成 operator delivery confirmation，并让 delivery gate 返回 success。
