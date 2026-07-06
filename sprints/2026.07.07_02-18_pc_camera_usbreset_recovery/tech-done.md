# 2026.07.07 02:18 PC camera usbreset recovery

sprint_type: micro

## 实际改动

- `onboard/scripts/camera_usb_recovery_smoke.py` 新增 `--usbreset-device`：从目标 `/dev/videoX` 反查当前 USB 设备，再读取 sysfs `busnum/devnum`，固定执行 `usbreset BBB/DDD`，并输出 `usbreset_requested/attempted/ok` 与完整 `usbreset` 证据。
- `onboard/scripts/upper_robot_api.py` 的 `/api/camera/usb-recovery` 新增 `usbreset_device` 布尔白名单，子进程超时放宽到 120s；恢复动作仍只作用于相机链路，不发送底盘运动命令。
- `pc-tools/workstation/src/server/index.ts`、`src/shared/contracts.ts` 新增 PC 代理透传与回显字段。
- `pc-tools/workstation/src/client/workstationApi.ts` 和 `RobotControlConsolePanel.vue` 让普通页面的一次性自动 USB recovery 携带 `usbreset_device=true`，并在 DOM 暴露 `data-auto-usb-recovery-usbreset-*`。
- 同步更新 `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/vision/board_camera_publisher.md`。

## 验证结果

- `python3 onboard/scripts/test_camera_usb_recovery_smoke.py`：10 tests passed。
- `python3 -m unittest onboard.tests.test_camera_usb_recovery_smoke`：5 tests passed。
- `npm test -- test/catalog.test.ts --run`：195 tests passed。
- `npm test -- test/robotControlSummary.test.ts --run`：18 tests passed。
- `npm run build`：通过；仅保留既有 Vite chunk size warning。
- 已部署到上位机 `root@192.168.1.11 -p 7878`，`trashbot-upper-robot-api.service` active，8787 health 返回 `status=ready`。
- 本地 PC Node 已重启并监听 `0.0.0.0:7001`，默认小车地址 `http://192.168.1.11:8787`。
- 真实 PC 代理复验：
  - 请求：`POST http://127.0.0.1:7001/api/robot-control/camera/usb-recovery` body `{"device":"/dev/video1","usbreset_device":true}`。
  - 返回：`proxy_status=recovery_forwarded`、`remote_http_status=200`、`usbreset_attempted=true`、`usbreset_ok=true`。
  - 相机恢复：`status=frame_observed`、`frame_observed=true`、`stream_failure_class=none`、`software_capture_exhausted=false`、`known_good_uvc_required=false`。
  - 安全边界：`hard_dangerous_true_fields=[]`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`opens_base_uart=false`、`sends_motion_commands=false`。
- 真实 PC MJPEG 入口复验：
  - `GET /api/robot-control/camera/mjpeg` 在 8 秒内收到 `4056284` 字节 multipart MJPEG，第一帧为 JPEG/JFIF。
  - `GET /api/robot-control/camera/mjpeg/status` 返回 `status=streaming`、`source_readiness=first_frame_observed`、`shared_preview_current_frame_visible=true`。
- 地图和手控复验：
  - summary `readback_summary.map` 返回 `map_current_visible=true`、`path_current_visible=true`、`radar_overlay_current_visible=true`、`route_target_visible=true`、`robot_pose_status=map_pose_observed`。
  - PC manual forward/back 短脉冲均 `proxy_status=command_forwarded`、`command_result_ok=true`、`stop_result_ok=true`、`command_raw_lr_nonzero_proven=true`；summary 返回 `keyboard_continuous_motion_verified=true`。

## 剩余风险

- DV20 会进入 USB 设备级卡死；现在 PC 自动恢复会做一次 `usbreset`，但如果物理供电/线材继续不稳定，仍可能再次卡死。
- `usbreset` 会短暂重连相机 USB 设备；本轮限定为相机-only 恢复，不影响 WAVE ROVER UART 或 `/cmd_vel`。
- 本轮未重新跑 Docker/ROS2 `colcon build`，因为改动集中在 PC Node、上车脚本和相机恢复代理，不涉及 ROS2 package 构建入口。
