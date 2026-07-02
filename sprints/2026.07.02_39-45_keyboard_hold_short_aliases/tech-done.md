# 键盘按住手控短别名

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间：2026-07-02 18:40 CST

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `keyboard_hold_*` 顶层短字段，复用 `current_keyboard_control_pack_*`，直接暴露键盘可复验状态、按住才动、松开后读回、缺失证据和点击/读回边界。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 PC 的 `plain-current-keyboard-control-pack` 同步暴露 `data-keyboard-hold-*`。
- `pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：补齐类型和合同测试。
- `docs/product/pc_tools_workstation.md`：记录 `keyboard_hold_*` 与键盘控制包同源，说明启用不发车、按住才发送连续低速脉冲。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，`1 passed`，`10 passed`。
- 通过：`npm test -- test/App.test.ts`，`1 passed`，`237 passed`。
- 通过：`npm run build`。Vite 仍提示既有大 chunk 警告，不影响构建产物。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001`，`/map` 返回 HTTP `200`。
- 通过：只读读取 `/api/robot-control/summary`，现场返回
  `keyboard_hold_status=ready_for_safety_confirm`、
  `keyboard_hold_action_id=hold_keyboard`、
  `keyboard_hold_ready=true`、
  `keyboard_hold_requires_safety_confirm=true`、
  `keyboard_hold_to_move_required=true`、
  `keyboard_hold_sends_motion_when_clicked=false`、
  `keyboard_hold_sends_motion_when_held=true`、
  `keyboard_hold_post_hold_readback_endpoints=[/api/robot-control/base/feedback-samples,/api/robot-control/summary]`。
- 通过：只读执行雷达贴图刷新链路保持 `robot_control_executed=false`、`safe_to_control=false`、
  `sends_motion_when_clicked=false`、`starts_nav2=false`、`starts_keyboard=false`、`starts_free_roam=false`；
  再读 summary 显示 `radar_map_wysiwyg_status=loaded`、`live_wysiwyg_missing_surface_ids=[camera]`。

## 剩余风险

- 本轮只提升 PC/summary 的键盘连续手控可读性，不替现场执行键盘按住动作；真实 wheel L/R 非零和松开停稳仍需要安全确认后实车验收。
- 现场仍显示 `camera_wysiwyg_status=needs_first_frame`；相机首帧仍未完成，继续阻塞建图；不影响键盘连续手控可先验收。
