# PC 相机恢复计划结构化

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增相机 WYSIWYG 恢复计划字段：`live_wysiwyg_camera_recovery_status`、`live_wysiwyg_camera_recovery_next_action_plain`、`live_wysiwyg_camera_recovery_sequence`、`live_wysiwyg_camera_recovery_sequence_labels`、`live_wysiwyg_camera_recovery_sends_motion`。
  - 当上车诊断已排除页面独占时，普通文案明确“相机不是页面独占”，下一步为复测首帧、读取共享预览状态；仍无帧时再检查 USB 线、接口、供电或换 known-good UVC。
  - 建图解锁字段同步复用该恢复计划，并固定只读 summary 回刷 endpoint。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-wysiwyg-diagnostics` 和 `plain-mapping-camera-unblock-plan` 暴露 `data-camera-recovery-*`、`data-fixed-summary-endpoint`，并显示相机恢复下一步。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 live closure summary 类型合同。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖 API 字段、普通首屏 DOM 字段和 no-motion 边界。
- `docs/product/pc_tools_workstation.md`
  - 记录相机恢复计划合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts test/App.test.ts -t "same-window wheel|plain-live-closure|stale radar"`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test -- --run`，结果 `Test Files 3 passed (3)`、`Tests 413 passed (413)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。
- 通过：重启 `PORT=7001 HOST=0.0.0.0 npm run api` 后只读 `GET http://127.0.0.1:7001/api/robot-control/summary` smoke：
  - `source_base_url=http://192.168.1.11:8787`
  - `status=needs_wheel_rerun`
  - `objective_done=1/4`
  - `camera_current_visible=false`
  - `mapping_start_ready=false`
  - `mapping_start_missing_reasons=[camera_first_frame]`
  - `live_wysiwyg_camera_recovery_status=not_exclusive_needs_source_check`
  - `live_wysiwyg_camera_recovery_next_action_plain=相机不是页面独占；先复测相机首帧并读取共享预览状态。若仍无画面，检查 USB 线、接口、摄像头供电或换 known-good UVC 后再复测。`
  - `live_wysiwyg_camera_recovery_sequence=[/api/robot-control/camera/first-frame/probe,/api/robot-control/camera/mjpeg/status,/api/robot-control/summary]`
  - `live_wysiwyg_camera_recovery_sends_motion=false`

## 剩余风险

- 本轮只改 PC 只读 summary/DOM/文案，没有实际修复物理 UVC/USB 首帧问题。
- 没有触发任何 Nav2、manual、keyboard、free-roam、delivery、stop、建图或 `/cmd_vel` 运动接口。
