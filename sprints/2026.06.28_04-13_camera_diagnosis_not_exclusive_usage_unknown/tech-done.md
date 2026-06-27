# 2026.06.28 04:13 相机 usage 未加载时仍显示非独占无帧

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏相机当前事实在 `source_diagnosis_status=uvc_no_frame_not_exclusive` 且设备名暂时未知时，不再生成 `摄像头 的 UVC` 这类生硬文案，改为 `UVC 没有输出视频帧`。
  - 该逻辑仍只消费只读 summary，不打开额外相机 reader，不发送运动、Nav2、free-roam、雷达或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 live 形状回归：`source_usage_status=not_loaded`、`selected_name=not_loaded`，但 diagnosis 已证明 `uvc_no_frame_not_exclusive` 时，普通首屏仍显示“共享预览支持多人观看、不是独占、UVC 没有输出视频帧”。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 usage 未加载但 diagnosis 已明确时的普通首屏相机口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "camera diagnosis when source usage is not loaded|live not-in-use camera first-frame failure"`，2 passed / 187 skipped。
- 通过：`cd pc-tools/workstation && npm test`，336 passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
  - Vite 仍提示生产包 chunk 大于 500 kB，这是既有前端体积提示，不影响本轮构建通过。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后，live 只读
  `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回
  `camera.status=source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_usage_status=not_in_use`、`selected_name=USB Composite Device: DV20 USB`、
  `source_diagnosis_status=uvc_no_frame_not_exclusive`、`shared_preview_contract=single_shared_capture_for_multiple_clients`、
  `shared_preview_exclusive_camera_claim=false`、`free_roam_motion_start_ready=true`、`free_roam_mapping_ready=false`、
  `free_roam_mapping_missing_reasons=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`、`robot_control_executed=false`。

## 剩余风险

- 本轮不修复 UVC 真实无帧问题，只保证普通首屏不会误判为页面独占。
- 摄像头首帧、雷达 fresh、Nav2 完整路线、同窗口轮速 L/R 非零和 delivery success 仍需后续现场验证。
