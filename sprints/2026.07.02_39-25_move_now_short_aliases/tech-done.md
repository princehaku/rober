# 可先动短别名

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间：2026-07-02 18:25 CST

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `current_move_now_*` 顶层短字段，复用安全确认队列和目标总览，直接给出可先动动作、主动作聚焦、建图阻塞、最小预检和点击边界。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 PC 的 `plain-current-safety-confirm-queue` 同步暴露 `data-current-move-now-*`，不新增第二套按钮体系。
- `pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：补齐类型和合同测试。
- `docs/product/pc_tools_workstation.md`：记录 `current_move_now_*` 与安全确认队列同源，卡片点击只聚焦不发车。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，`1 passed`，`10 passed`。
- 通过：`npm test -- test/App.test.ts`，`1 passed`，`237 passed`。
- 通过：`npm run build`。Vite 仍提示既有大 chunk 警告，不影响构建产物。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001`，`/map` 返回 HTTP `200`。
- 通过：只读读取 `/api/robot-control/summary`，现场返回
  `current_move_now_status=ready_for_safety_confirm`、
  `current_move_now_action_ids=[run_nav2_route,hold_keyboard,start_free_move]`、
  `current_move_now_primary_action_id=run_nav2_route`、
  `current_move_now_primary_focus_kind=trip_safety_confirm`、
  `current_move_now_sends_motion_when_clicked=false`、
  `current_move_now_starts_nav2_when_clicked=false`、
  `current_move_now_minimal_precheck_safety_only=true`、
  `current_move_now_camera_preflight_required=false`、
  `current_move_now_radar_preflight_required=false`。

## 剩余风险

- 本轮只提高 PC/summary 的“可先动”可读性，不替用户执行 Nav2、键盘连续手控或自由移动；这些动作仍需要现场安全确认后手动触发。
- 现场仍显示 `camera_wysiwyg_status=needs_first_frame`；相机首帧仍是建图阻塞。`current_move_now_*` 只说明该阻塞不挡低速自由移动或已 ready 的运动验收。
