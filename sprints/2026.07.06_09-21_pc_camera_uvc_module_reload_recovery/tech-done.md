# 2026.07.06 09:21 PC camera UVC module reload recovery

sprint_type: micro

## 实际改动

- `onboard/scripts/camera_usb_recovery_smoke.py` 新增 `--reload-uvc-module`，显式记录 UVC 模块参数、`/dev/video*` 节点和 `modprobe` 返回值；该开关固定执行 `modprobe -r uvcvideo` 与 `modprobe uvcvideo quirks=0 nodrop=0 timeout=5000`，默认关闭。
- `onboard/scripts/upper_robot_api.py` 的 `/api/camera/usb-recovery` 新增 `reload_uvc_module` 布尔白名单，并把 recovery 子进程超时从 48s 放宽到 96s，避免模块重载加六组 STREAMON 被提前杀掉。
- `pc-tools/workstation/src/server/index.ts` 与 `src/shared/contracts.ts` 新增 PC 代理透传和回显字段：`uvc_module_reload_requested/attempted/ok`、`uvc_module_parameters_after_reload`、`uvc_module_reload`。
- 同步更新 PC 代理测试、上车脚本 no-hardware 测试，以及 `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/vision/board_camera_publisher.md`。

## 验证结果

- `python3 onboard/scripts/test_camera_usb_recovery_smoke.py`：9 tests passed。
- `python3 -m unittest onboard.tests.test_camera_usb_recovery_smoke`：4 tests passed。
- `npm test -- test/catalog.test.ts --run`：195 tests passed。
- `npm run build`：通过；仅保留既有 Vite chunk size warning。
- 已部署到上位机 `root@192.168.1.11 -p 7878`，并重启 `trashbot-upper-robot-api.service`；8787 health 返回 `status=ready`。
- 本地 PC Node 已重启并监听 `0.0.0.0:7001`，health 默认小车地址为 `http://192.168.1.11:8787`。
- 真实 PC 代理复验：
  - 请求：`POST http://127.0.0.1:7001/api/robot-control/camera/usb-recovery` body `{"device":"/dev/video1","reload_uvc_module":true}`。
  - 返回：`proxy_status=recovery_forwarded`、`remote_http_status=200`、`uvc_module_reload_ok=true`、`uvc_module_parameters_after_reload={quirks:0,nodrop:0,timeout:5000}`。
  - 相机仍无真实帧：`status=streamon_success_zero_byte_no_frame`、`frame_observed=false`、`usb_video_speed=480M`、`stream_failure_class=high_speed_zero_byte_no_frame`、`software_capture_exhausted=true`、`known_good_uvc_required=true`。
  - 安全边界：`hard_dangerous_true_fields=[]`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`opens_base_uart=false`、`sends_motion_commands=false`。
- 恢复后上位机服务确认：`trashbot-local-webrtc-camera.service active`、`trashbot-upper-robot-api.service active`、8088 与 8787 均监听。
- PC 状态确认：`GET /api/robot-control/camera/mjpeg/status` 返回 `source_first_frame_failed` / `uvc_no_frame_not_exclusive`，`camera_input_signal_check_required=true`、`known_good_uvc_required=true`、`software_capture_exhausted=true`。
- 地图读回保持可用：summary 的 `readback_summary.map` 返回 `map_current_visible=true`、`path_current_visible=true`、`radar_overlay_current_visible=true`、`route_target_visible=true`。
- 交付闭环读回保持可用：`GET /api/robot-control/delivery/latest` 返回 `delivery_success=true`、`status=delivery_success_confirmed`。

## 剩余风险

- 实时图传仍未完成：在页面独占、低速 USB、UVC quirk、V4L2 控制项、mmap/userptr/no-query 和 uvcvideo 模块状态漂移均排除后，DV20 仍不输出 video buffer。
- 下一步需要现场检查 DV20 输入信号、视频线/接口/供电、采集设备本体，或接入 known-good UVC 做对照复测。
- 本轮只验证真实上位机相机链路和 PC 代理；未重新跑 Docker/ROS2 `colcon build`，因为改动不涉及 ROS2 package 构建入口。
