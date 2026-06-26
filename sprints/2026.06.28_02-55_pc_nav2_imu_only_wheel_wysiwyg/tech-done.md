# PC Nav2 IMU-only wheel WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增行程轮速复验提示：当最近路线已返回成功、已发非零底盘命令且 IMU 姿态有变化，但 `base_feedback_lr_nonzero_proven=false`、latest L/R 仍为 `0/0` 时，普通地图 caption、行程进度和行程摘要都会显示“轮速 L/R=0/0 待复验”。
  - 保留“已到达”和“底盘已响应”的可见状态，但不把 IMU-only 运动迹象外推成 wheel raw L/R 非零，也不自动确认送达。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 IMU-only 到达回归：覆盖 `goal_succeeded + feedback_sample_count=239 + base_command_nonzero_count=49 + IMU delta + L/R=0/0`，确认 PC 仍显示到达，同时把轮速缺口放到普通首屏。
- `docs/product/pc_tools_workstation.md`
  - 记录普通 PC 界面对 Nav2 到达、IMU 运动迹象和 wheel raw L/R 复验的分层口径。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "IMU-only route arrival|summary latest Nav2 execution"`，`Tests 2 passed | 258 skipped (260)`。
- 已通过：`cd pc-tools/workstation && npm test`，`Tests 260 passed (260)`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。
  - 保留既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`。
- 已通过：`git diff --check`。

## 剩余风险

- 本轮只修 PC WYSIWYG 与回归测试，不执行真实发车命令，不宣称真实轮速非零或 delivery success。
- 真实小车如果继续 `L/R=0/0`，仍需现场复查电机使能、供电、底盘模式、控制模式和 WAVE ROVER 反馈链路。
