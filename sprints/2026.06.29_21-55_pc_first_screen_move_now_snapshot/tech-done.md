# PC first screen move-now snapshot

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏在“当前事实”后新增
  “现在可以做什么”摘要条，直接展示三件事：现在可先动、发车前确认、建图条件。
  该摘要只消费 `goal_checklist_summary` 的只读字段；按钮只滚动/聚焦到既有自由移动、安全确认或建图入口。
- `pc-tools/workstation/src/styles.css`：为摘要条新增紧凑样式和移动端单列布局。
- `pc-tools/workstation/test/App.test.ts`：补充首屏回归，确认摘要条可见、无工程词、点击跳转不触发任何 API。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录普通首屏口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，
  结果 `1 passed | 217 skipped`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `83363`。
- 通过：只读 live `GET http://127.0.0.1:7001/api/robot-control/summary` 返回
  `move_now_status_plain=可先动：自由自助移动、键盘连续手控、完整行程执行；发车前只需现场安全确认；相机和雷达只影响建图验收。`、
  `safety_precheck_summary_plain=发车前预检已精简：只需要现场安全确认...`、
  `mapping_blockers_plain=建图缺口：画面所见即所得、雷达点贴到地图、传感器就绪后建图...`，
  且 `first_motion_source_card_id=free_move`、`safety_precheck_source_card_id=free_move`、`mapping_source_card_id=mapping_start`。

## 剩余风险

- 本轮是 PC 首屏可用性改进，不执行真实运动、不修复 camera first frame、LiDAR fresh proof 或 Nav2 wheel L/R 闭环。
- 摘要条按钮只聚焦，不自动勾选安全确认，也不发送 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
