# PC Nav2 Pose WYSIWYG Gate

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏执行当前图上路线前，除了路线已经画在地图上，还要求小车 map-frame 位置也能显示在当前地图上。
  - 当路线可见但小车位置未显示时，行程状态改为 `待定位`，执行按钮显示 `先重新定位` 并保持禁用；当前事实、本轮进度、最小确认和路线 WYSIWYG 文案都提示先重新定位或刷新地图。
  - 该 gate 只收紧普通首屏 Nav2 路线执行，不自动调用定位重置、Nav2 execute、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/src/styles.css`
  - 增加 `待定位` 行程状态样式，和待确认/待准备同类显示。
- `pc-tools/workstation/test/App.test.ts`
  - 更新无小车位置的路线叠图回归：路线仍显示，但执行按钮禁用，点击不会产生 `/api/robot-control/nav2/goal/execute`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录当前路线执行必须满足“路线和小车位置都可见”的地图所见即所得口径。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "blocks execution when robot pose is missing" --maxWorkers=1 --no-fileParallelism`
  - `Tests 1 passed | 320 skipped (321)`。
- 已通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - `Test Files 2 passed (2)`，`Tests 321 passed (321)`。
- 已通过：`cd pc-tools/workstation && npm run lint`
  - 无 ESLint 报错。
- 已通过：`cd pc-tools/workstation && npm run build`
  - `vite build` 完成；保留既有 chunk size warning。
- 已通过：`git diff --check`
  - 无空白错误。

## 剩余风险

- 本轮不执行真实 Nav2 路线、不恢复 Nav2 planner/controller、不发送任何运动或 stop 命令。
- 当前 live 上位机仍显示相机 UVC 无首帧、雷达 runtime stale、Nav2 planner/controller inactive 和 wheel raw L/R 非零未证明；本轮只防止 PC 在小车位置不可见时继续放行图上路线执行。
