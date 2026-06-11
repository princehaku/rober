# 2026-06-11 23:30 PC Plain Motion Readiness Hint

## sprint_type

micro

## 设计边界

- 目标是把非 stop 运动 gate 的缺口转成普通首屏下一步提示。
- 普通首屏只显示 `待检查` 和 `移动前先完成画面、轮子和周围环境检查；需要时可直接停止。`。
- 不在首屏展示 `operator_report`、`physical_motion_lidar_delta_proven`、endpoint、raw/readback、
  HIL、proof、`/api/base/manual` 或方向按钮。
- 本轮不调用真实 `/api/base/manual`，不发布 `/cmd_vel`，不执行 NavigateToPose，不放宽
  非 stop 运动 gate。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 `移动/导航` 卡片读取
  现有 `operatorMaterialReady`，缺运动前材料时显示普通检查提示；材料齐备时显示
  `已完成移动前检查；需要时可直接停止。`。
- `pc-tools/workstation/test/App.test.ts`：更新默认首屏断言，新增不完整材料和完整材料下的
  普通首屏文案断言，确保工程字段不外泄。
- `docs/product/pc_tools_workstation.md`：同步普通首屏移动/导航契约。

## 验证结果

- `cd pc-tools/workstation && npm run test -- App.test.ts`：通过，17 tests。
- `cd pc-tools/workstation && npm run test`：通过，2 files / 93 tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc`。
- `cd pc-tools/workstation && npm run lint`：通过，ESLint 无报错。

## 剩余风险

- 这只是 PC 首屏 readiness 提示，不执行真实手动移动。
- 非 stop 运动仍必须等待 visible camera、外部视频、轮速反馈非零和 LiDAR motion delta 材料。
