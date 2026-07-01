# Camera WYSIWYG Recovery Aliases

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增相机 WYSIWYG 恢复 alias：`camera_wysiwyg_recovery_status`、`camera_wysiwyg_recovery_next_action_plain`、`camera_wysiwyg_recovery_readback_endpoints`、`camera_wysiwyg_recovery_readback_sequence_labels`、`camera_wysiwyg_recovery_requires_usb_fix`、`camera_wysiwyg_recovery_blocks_mapping_start`、`camera_wysiwyg_recovery_blocks_free_move`、`camera_wysiwyg_recovery_sends_motion`、`camera_wysiwyg_recovery_starts_map_runtime` 等。
- 普通首屏 `plain-live-closure-summary` DOM 同步暴露 `data-camera-wysiwyg-recovery-*`，现场脚本不用解析多段相机/建图字段即可确认：相机缺口只阻塞建图首帧，不阻塞自由移动；恢复读回只读且不发车。
- 更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，明确换高速 USB 或共享预览复验后的固定链路为 `camera/first-frame/probe -> camera/mjpeg/status -> summary`，且不启动独占相机、建图 runtime、Nav2/manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts robotControlSummary.test.ts`，结果 `2 passed (2)`、`246 passed (246)`。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`，生成 `dist/assets/index-CyjDZnPi.js`；Vite 仅保留既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001`，`lsof` 显示 `node ... TCP *:7001 (LISTEN)`。
- 通过：运行实例 `curl /api/robot-control/summary` 读到 `camera_wysiwyg_recovery_readback_endpoints=["/api/robot-control/camera/first-frame/probe","/api/robot-control/camera/mjpeg/status","/api/robot-control/summary"]`、`camera_wysiwyg_recovery_requires_usb_fix=true`、`camera_wysiwyg_recovery_blocks_mapping_start=true`、`camera_wysiwyg_recovery_blocks_free_move=false`、`camera_wysiwyg_recovery_sends_motion=false` 和 `camera_wysiwyg_recovery_starts_map_runtime=false`。
- 通过：前端 bundle grep 到 `data-camera-wysiwyg-recovery-readback-endpoints`、`data-camera-wysiwyg-recovery-requires-usb-fix`、`data-camera-wysiwyg-recovery-blocks-mapping-start`、`data-camera-wysiwyg-recovery-blocks-free-move`、`data-camera-wysiwyg-recovery-sends-motion`、`data-camera-wysiwyg-recovery-starts-map-runtime`。
- 只读硬件复验：`POST /api/robot-control/camera/first-frame/probe` 由上车返回 503，body 显示 `open_ok=true`、`read_ok=false`、`first_frame_timeout=true`、`failure_reason=deadline_expired`、`robot_control_executed=false`；随后 `camera/mjpeg/status` 和 summary 稳定读回 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`source_diagnosis_not_exclusive=true`、`exclusive_camera_claim=false`。

## 剩余风险

- 当前相机仍未出首帧，真实状态是 USB full-speed / UVC 无帧方向；需要现场换高速 USB 口/线或带供电 Hub 后再次复验。
- 本轮没有新的现场安全确认，未发送 Nav2、keyboard、free-roam、mapping、delivery、stop 或 `/cmd_vel`；真实 wheel L/R 非零、delivery success 和自由移动/建图闭环仍待现场安全确认后验证。
