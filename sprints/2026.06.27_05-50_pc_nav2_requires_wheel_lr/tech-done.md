# PC Nav2 完整路线要求同窗口 wheel L/R

- sprint_type: micro
- owner: full-stack-software-engineer
- 时间：2026-06-27 05:50

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：收紧 `nav2ExecutionControlProven`，当 Nav2 latest 明确给出 `base_feedback_lr_nonzero_proven=false` 或 `wheel_feedback_lr_nonzero_proven=false` 时，不再把 `goal_succeeded`、IMU 姿态变化或非零底盘命令当成完整路线完成。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：LiDAR summary 优先消费 endpoint `key_values.latest_proof_status`，避免真实 `raw_packets_parsed` 被顶层 `status=loaded` 覆盖。
- 普通首屏 `当前事实`、地图行程 label、行程进度和送达 gate 文案同步改为“路线返回成功，但同窗口轮速未证明 / 到达未证明”，避免普通用户把 action success 误读成小车真实到达。
- `pc-tools/workstation/test/App.test.ts`：更新 IMU-only、zero wheel 和 explicit unproven Nav2 用例，锁住“IMU 可见但不能替代 wheel raw L/R”的行为。
- `pc-tools/workstation/test/catalog.test.ts`：新增 raw packet parsed summary 回归，锁住真实 7001 的 LiDAR WYSIWYG 字段。
- `docs/product/pc_tools_workstation.md`：记录该判定边界。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts`（150 passed）
- 通过：`npm test -- --run test/catalog.test.ts`（113 passed）
- 通过：`npm run lint`
- 通过：`npm run build`（Vite 仅提示现有 chunk size warning）
- 通过：`git diff --check`

## 剩余风险

- 本轮是 PC 判定和文案修正，不等于真实 Nav2 底盘闭环已修好。
- 现场 live 仍显示 Nav2 已发非零命令、IMU 有变化，但同窗口 wheel L/R 为 0/0；下一步仍要查底盘使能、供电、控制模式和 Nav2 执行窗口反馈采集。
