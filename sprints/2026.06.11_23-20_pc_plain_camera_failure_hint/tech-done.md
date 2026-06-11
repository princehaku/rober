# 2026-06-11 23:20 PC Plain Camera Failure Hint

## sprint_type

micro

## 设计边界

- 目标是把真实上位机 `source_first_frame_failed` 转成普通用户能处理的首屏提示。
- 普通首屏只能显示 `失败` 和 `相机没有出画面，检查摄像头/视频线。`。
- `source_readiness`、`first_frame_timeout`、`/dev/video1`、offer/peer/SDP 等工程细节仍只在
  默认关闭的高级诊断中展示。
- 本轮不新增上位机 endpoint，不自动打开 WebRTC peer，不触发首帧探针，不调用
  `/api/base/manual`，不发布 `/cmd_vel`，不放宽运动 gate。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增相机源失败的普通提示
  helper；当 summary 显示 `source_first_frame_failed` 或 `first_frame_timeout` 时，首屏
  `实时画面` 卡片显示普通失败提示。
- `pc-tools/workstation/test/App.test.ts`：新增首屏回归，断言普通提示可见，同时
  `source_readiness`、`first_frame_timeout`、`/dev/video1` 不进入首屏。
- `docs/product/pc_tools_workstation.md`：同步普通用户简易控制契约。

## 验证结果

- `cd pc-tools/workstation && npm run test -- App.test.ts`：通过，17 tests。
- `cd pc-tools/workstation && npm run test`：通过，2 files / 93 tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc`。
- `cd pc-tools/workstation && npm run lint`：通过，ESLint 无报错。

## 剩余风险

- 这只是 PC 普通首屏提示修正，不恢复 `/dev/video1` 首帧，也不证明实时图传可见内容。
- 非 stop 运动 gate 仍需 visible camera、外部视频、轮速反馈非零和 LiDAR motion delta 材料。
