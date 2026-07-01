# Camera Status Hardware Alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/camera/mjpeg/status` 从只读 `/api/camera/health` 提取 `uvc_usb_topology`，并在顶层暴露画面硬件恢复 alias、建图/自由移动阻塞边界和固定复测端点。
- `pc-tools/workstation/src/shared/contracts.ts`：同步 `RobotControlCameraMjpegStatusResponse` 字段。
- `pc-tools/workstation/test/catalog.test.ts`：扩展 full-speed USB 诊断测试，锁定 `camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_blocks_mapping_start=true` 和 `camera_blocks_free_move=false`。
- `docs/product/pc_tools_workstation.md`：记录 camera status 顶层 alias 与 no-motion 边界。

## 验证结果

- 通过：`npm test -- --run test/catalog.test.ts -t "workstation camera MJPEG status translates full-speed USB diagnosis"`，1 passed。
- 通过：`npm test`，3 files / 420 tests passed。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：PC Node 已重启到 `0.0.0.0:7001`，新 PID `62402`。
- 通过：只读 curl `/api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=status_loaded`、`source_readiness=first_frame_failed`、`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`source_diagnosis_not_exclusive=true`、`source_usage_scope=free`、`shared_preview_exclusive_camera_claim=false`、`uvc_usb_topology_video_usb_speed=12M`、`camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`camera_recovery_sends_motion=false`、`camera_recovery_starts_map_runtime=false`、`camera_status_readback_only=true`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补只读 camera status 合同，不恢复物理相机首帧，不打开独占相机，不启动建图 runtime，也不触发 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 完整目标仍未收口：真实画面首帧、雷达贴图新鲜态、同窗口 wheel L/R 非零、delivery success、键盘连续手控和自由移动运行态仍需现场材料。
