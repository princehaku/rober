# PC Nav2 Latest Key Values Readback Micro Sprint

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/nav2/goal/execution/latest` 新增 `latest_key_values` 统一读数包，保留原始 `goal_execution_key_values` 并加入 PC 推导出的下一次执行模式、wheel raw L/R、非零命令计数和白话下一步。
- 同步更新共享 contract 与 catalog 测试，确保独立 latest 入口可以机器可读地暴露“上次路线成功但 wheel raw L/R 未非零，下一次用 ROS 模式重跑复验”。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录该变化只读取 latest artifact，不触发 Nav2 execute、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Nav2 latest execution proxy"`，4 passed，156 skipped。
- 通过：`npm --prefix pc-tools/workstation run build`，Vite build 成功；仅保留既有 chunk size warning。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部 passed。
- 通过：PC API 已重启到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `*:7001`。
- 通过：只读读取 `http://127.0.0.1:7001/api/robot-control/nav2/goal/execution/latest?baseUrl=http://192.168.1.11:8787`，`latest_key_values` 返回 `status=goal_succeeded`、`base_command_mode=pwm`、`next_execution_base_command_mode=ros`、`goal_execution_base_command_nonzero_count=49`、`goal_execution_base_feedback_lr_nonzero_proven=false`、`goal_execution_base_feedback_latest_raw_left=0`、`goal_execution_base_feedback_latest_raw_right=0`，下一步为“勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认 wheel raw L/R 非零”。

## 剩余风险

- 当前改动只是补全 Nav2 latest 只读合同，不等于已经现场重跑完整图上路线，也不证明本轮 wheel raw L/R 已非零。
- 未经现场安全确认，本轮不调用 `/api/robot-control/nav2/goal/execute`、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel` 控制接口。
