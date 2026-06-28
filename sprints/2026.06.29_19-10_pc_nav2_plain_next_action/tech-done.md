# 2026-06-29 19:10 PC Nav2 下一步白话化

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `safe_command_boundary` 新增 `nav2_goal_next_action_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 为 Nav2 行程边界生成普通用户白话下一步。
  - 将 `wheel raw L/R` 转为“执行窗口轮速 L/R”，将 `ROS/PWM/SPEED` 转为“ROS/PWM/SPEED 模式”，将 `controller` 转为“控制服务”。
  - 保留原 `nav2_goal_next_action` 工程字段，避免破坏已有诊断和脚本。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏读取 Nav2 下一步时优先使用 `nav2_goal_next_action_plain`；旧 summary 缺字段时继续本地翻译。
  - 旧 summary 出现 plain 默认短句但 raw 已包含更具体重跑/恢复服务动作时，按 raw 生成普通话，避免把“先生成路线”误当成唯一下一步。
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
  - 增加/同步 Nav2 白话字段断言和 fixture。
- `pc-tools/README.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 Nav2 行程下一步白话字段和安全边界。

## 验证结果

- 已通过：
  - `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Nav2"`
  - `npm --prefix pc-tools/workstation test -- App.test.ts -t "IMU-only|managed Nav2 runtime|ROS T13|stopped Nav2 stack"`
  - `npm --prefix pc-tools/workstation test`
  - `npm --prefix pc-tools/workstation run build`
- `npm --prefix pc-tools/workstation test` 结果：2 个测试文件通过，373 个测试通过。
- `npm --prefix pc-tools/workstation run build` 结果：TypeScript、Vite client build、server TypeScript 通过；Vite 仍提示 bundle chunk 超过 500 kB，属于既有构建提醒。
- 已重启 PC workstation API，`0.0.0.0:7001` 当前由 `npm run api` / `tsx src/server/index.ts` 监听。
- 只读 live 验证：
  - `curl -sS --max-time 22 http://127.0.0.1:7001/api/robot-control/summary`
  - `robot_api_connection.status=readable`
  - `safe_command_boundary.nav2_goal_next_action` 保留工程字段：`wheel raw L/R`、`controller`。
  - `safe_command_boundary.nav2_goal_next_action_plain` 返回普通字段：`执行窗口轮速 L/R`、`控制服务`、`ROS 模式`。
  - 摄像头仍返回 `source_first_frame_failed`，下一步为检查 USB、摄像头输入或供电；共享预览不是页面独占。
  - 地图雷达 overlay 仍是 `not_current`，下一步为先启动雷达再刷新地图画面。

## 剩余风险

- 本轮不执行真实 Nav2 goal，不发送 manual、keyboard、free-roam、delivery、stop、雷达 start 或 `/cmd_vel`。
- live 仍显示旧路线 action 成功但执行窗口轮速 L/R 为 `0/0`，完整 Nav2 路线执行和 wheel raw L/R 非零仍需要现场安全确认后重跑验证。
