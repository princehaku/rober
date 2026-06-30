# PC 建图相机阻塞解锁提示

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `RobotControlLiveClosureSummary` 中新增建图未就绪时的相机/雷达阻塞解释字段、固定只读复测 endpoint 和 no-motion 边界字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从 `mapping_start_missing_reasons` 派生普通用户文案，明确相机首帧/雷达 fresh 只阻塞建图启动和验收，不阻塞安全确认后的自由移动；同时带出相机诊断状态和下一步只读复测入口。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-live-closure-summary` 与 `plain-mapping-camera-unblock-plan` 同步暴露上述 API 字段，页面只展示/聚焦，不启动建图、自由移动或 Nav2。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：补 API 与 DOM 断言，锁定自由移动不被相机/雷达缺口阻塞、建图缺口提示只读且不发运动命令。
- `docs/product/pc_tools_workstation.md`：同步 PC 工作站合同。

## 验证结果

- 已通过：`npm test -- --run test/robotControlSummary.test.ts`，1 file / 6 tests。
- 已通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 matched test；`npm test -- --run test/App.test.ts -t "uses camera diagnosis when source usage is not loaded"`，1 matched test。
- 已通过：`npm run build`，`tsc` + Vite build + server `tsc` 通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积 warning。
- 已通过：`npm test -- --run`，3 files / 413 tests。
- 已通过：`npm run lint`，0 error；仍有 `RobotControlConsolePanel.vue` 4 个既有 `vue/multiline-html-element-content-newline` warning。
- 已通过：`git diff --check`。
- 已通过：重启 PC Node 到 `0.0.0.0:7001`，实际监听进程 `node` PID `57554`；只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `status=needs_wheel_rerun`、`mapping_start_ready=false`、`mapping_start_missing_reasons=camera_first_frame`、`mapping_camera_blocks_start=true`、`mapping_lidar_blocks_start=false`、`mapping_unblock_allows_free_move=true`、`mapping_unblock_camera_diagnosis_status=uvc_transport_error_not_exclusive`、`mapping_unblock_camera_not_exclusive=true`、固定相机 probe/MJPEG status endpoint 和 `mapping_unblock_sends_motion_when_clicked=false`。
- 修复中发现并已回归：第一次全量测试发现普通首屏可见文案泄漏 `uvc_no_frame_not_exclusive` 工程 token；已改为 `mapping_start_unblock_plain` 只显示中文相机提示，工程 token 仅保留在 API/DOM 的机器可读字段。

## 剩余风险

- 当前改动只修 PC API/DOM 可见合同和普通用户提示，不会修复真实 UVC `error -71` 或摄像头首帧缺失本身。
- 未经新的现场安全确认，本轮不会执行自由移动、Nav2、建图启动、键盘手控、stop 或任何 `/cmd_vel` 运动链路。
