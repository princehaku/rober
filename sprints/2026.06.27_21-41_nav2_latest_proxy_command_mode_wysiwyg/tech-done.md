# Nav2 Latest Proxy Command Mode WYSIWYG

sprint_type: micro

## 实际改动

- 修正 `GET /api/robot-control/nav2/goal/execution/latest` 的只读证据解析：兼容现场上车 artifact 中 `base_command_summary.latest_nonzero_command.command_mode` 的 live 形状。
- 当上车 artifact 有 `nonzero_command_count>0` 但没有 `command_mode_counts` 时，PC latest proxy 会按 `pwm/ros/speed` 合成短摘要，避免“已发非零底盘命令”在路线详情里掉成 `not_loaded/{}`。
- 新增 catalog 回归测试，覆盖 Nav2 action succeeded、非零 PWM 命令 49 条、wheel raw L/R 仍 0/0 的现场形状；该测试同时确认 latest 读取不重放 Nav2、不调用 manual。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录 summary 与 latest proxy 的一致证据口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "Nav2 latest execution proxy"`，1 个文件通过，4 个命中测试通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个文件通过，314 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍有单 chunk 超过 500 kB 的既有体积提醒。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修只读证据所见即所得，不执行真实 Nav2 路线、不发 `/cmd_vel`，也不证明 wheel raw L/R 已在路线执行窗口非零。
