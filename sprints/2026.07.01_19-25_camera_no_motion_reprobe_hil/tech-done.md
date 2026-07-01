# 相机画面 no-motion 复测

sprint_type: micro

## 实际改动

- 本轮不改产品代码，只执行固定 no-motion 相机复测链路：`POST /api/robot-control/camera/first-frame/probe`、`GET /api/robot-control/camera/mjpeg/status`、`GET /api/robot-control/live-summary`。
- 复测后再次执行 no-motion `POST /api/robot-control/radar/scan-proof/refresh`，避免相机复测后建图条件里的雷达新鲜度回退。
- 全程不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`POST http://127.0.0.1:7001/api/robot-control/camera/first-frame/probe` 返回 `status=blocked`、`proxy_status=probe_failed`、`failure_reason=The operation was aborted due to timeout`。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status` 返回 `status=idle_not_started`、`client_count=0`、`upstream_active=false`、`exclusive_camera_claim=false`、`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`source_diagnosis_not_exclusive=true`。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/live-summary` 返回 `camera_current_visible=false`、`camera_first_frame_probe_status=blocked`、`camera_first_frame_failure_reason=The operation was aborted due to timeout`、`camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_source_diagnosis_not_exclusive=true`、`camera_shared_preview_exclusive_camera_claim=false`、`camera_usb_speed=12M`。
- 通过：相机复测后顺序刷新雷达 proof，最终 `live-summary` 返回 `radar_map_points_visible=true`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=155`、`mapping_start_missing_reasons=["camera_first_frame"]`。
- 通过：PC Node 仍监听 `0.0.0.0:7001`。

## 剩余风险

- 画面 WYSIWYG 仍未完成；当前证据指向硬件链路问题，不是页面独占：USB 摄像头挂在 `12M` full-speed，首帧 probe timeout。下一步需要现场换高速 USB 口/线或带供电 USB Hub 后再复测。
- 建图启动仍只差 `camera_first_frame`；完整 Nav2 路线、键盘连续手控和 delivery success 仍需要现场安全确认后执行并读回。
