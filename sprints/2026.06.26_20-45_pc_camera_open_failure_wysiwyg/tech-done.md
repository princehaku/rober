# PC 实时画面打开失败所见即所得

## sprint_type

micro

## 背景

- live 7001 summary 显示相机服务 `status=ready`、`devices_status=loaded`，但 `last_offer_failure_reason=opencv_capture_not_opened`。
- 原普通首屏可能继续显示“相机在线，点打开画面”，不能直观看出最近一次打开真实画面失败。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `cameraSourcePlainFailureHint` 现在消费 `last_offer_failure_reason/last_offer_error`。
  - `cameraOfferPlainFailureHint` 新增 `opencv_capture_not_opened/capture_not_opened/camera_open_failed` 翻译，显示 `相机没有打开；检查摄像头/视频线或占用后重试。`
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `shows camera open failure from readback instead of plain online copy`。
  - 断言普通首屏显示相机打开失败，不暴露原始字段，不调用 camera offer、Nav2、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录相机最近打开失败的普通首屏口径和安全边界。

## 验证结果

- `npm test -- -t "camera open failure|camera readback is online|camera source first-frame"`：首次失败，定位到 `last_offer_error="none"` 被误当成真实失败原因；已修复为忽略 `none/not_loaded`。
- `npm test -- -t "camera open failure|camera readback is online|camera source first-frame"`：修复后通过，1 个 test file，4 passed，207 skipped。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 保留既有 `Some chunks are larger than 500 kB` warning。
- `npm test`：通过，2 个 test file，211 passed。
- 全量测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，已用精确 patch 恢复，避免把测试副作用纳入本轮提交。

## 剩余风险

- 本轮是 PC 首屏状态显示和 mock 单元验证，未做真实相机重新打开 HIL。
- 该改动只展示最近相机打开失败，不自动重试 camera offer；现场仍需检查摄像头/视频线/占用后手动再打开。
