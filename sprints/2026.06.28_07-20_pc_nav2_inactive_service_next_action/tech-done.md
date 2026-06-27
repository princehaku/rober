# Tech Done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 新增 Nav2 inactive 服务名提取：planner inactive 显示“规划服务”，controller inactive 显示“控制服务”。
  - 自动驾驶未准备好且 planner/controller inactive 时，下一步从“先准备图上行程”改为“先恢复规划服务/控制服务，再准备图上行程并按地图画面确认”。
  - “恢复自动驾驶服务（不发车）”状态使用中文服务名，避免普通用户看到 planner/controller 英文诊断。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 planner-only blocker 的普通首屏断言。
  - 增加 planner+controller inactive 时恢复状态和当前事实的断言。
- `docs/product/pc_free_roam_mapping_design.md`
  - 补充 2026-06-28 07:20 的 PC Nav2 inactive 服务诊断规则。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "Nav2|nav2|plain trip|行程|自动驾驶服务|planner" --maxWorkers=1 --no-fileParallelism`
  - 结果：2 个 test files，51 passed，273 skipped。
- 已通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - 结果：2 个 test files，324 passed。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - 备注：Vite 输出既有 `Some chunks are larger than 500 kB` 警告；构建命令退出码为 0。
- 已通过：`git diff --check`

## 剩余风险

- 本轮只修普通 PC 端“自动驾驶为什么不能动”的诊断和恢复入口文案，没有在真实小车上发起 Nav2 路线执行。
- 当前现场 7001 读数仍显示 planner/controller inactive；真实完整路线执行需要先恢复 Nav2 服务，并在操作员明确安全确认后再做运动验证。
- 相机和雷达状态不再被当作底盘试动前置条件，但建图 ready 仍需要真实相机帧和 fresh 雷达读数。
