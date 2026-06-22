# Restore First-Jog Material Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通 `移动/导航` 卡片新增 `恢复试动确认` 按钮。
  - 当 latest operator report 是送达草稿一类状态，且已有视觉材料但 first-jog 缺基础安全确认时，允许现场人员一键恢复 first-jog 前置 operator report。
  - 恢复请求只复用 summary 中明确 `true; ref=...` 的外部视频/相机 ref，并写入 `operator_present=true`、`physical_clearance_confirmed=true`、`emergency_stop_ready=true`。
  - 恢复请求继续写 `wheel_feedback_lr_nonzero_proven=false`、`physical_motion_lidar_delta_proven=false`、`delivery_success=false`，不触发运动。
- `pc-tools/workstation/test/App.test.ts`
  - 新增测试覆盖 `恢复试动确认`：断言只提交固定 operator report，不调用 first-jog/manual。
- `docs/product/pc_tools_workstation.md`
  - 同步记录该入口解决的送达草稿覆盖 first-jog readiness 问题和安全边界。

## 当前真实状态

- PC summary 显示当前上位机 latest operator report 为 `delivery-draft-smoke-1782102952`。
- `first_jog_readiness_summary.status=blocked_missing_basic_safety`。
- `visual_material_ready=true`，缺项为 `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`。
- 因此本轮先补 PC 恢复路径，不在无人确认现场的情况下发送真实 first-jog。

## 验证结果

- `npm test`
  - 通过：`Test Files 2 passed (2)`，`Tests 111 passed (111)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。

## 剩余风险

- 本轮未执行真实运动，wheel raw L/R 非零仍未完成。
- `恢复试动确认` 需要现场人员点击确认；它不是自动安全判定，也不是 HIL pass。
- delivery success 仍不能宣称完成。
