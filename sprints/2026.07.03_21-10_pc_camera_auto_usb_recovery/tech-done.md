# PC camera auto USB recovery

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/client/workstationApi.ts`：新增固定 `POST /api/robot-control/camera/usb-recovery` client 调用；前端只传 `baseUrl`，不允许浏览器拼接任意 shell 参数或上车路径。
- `pc-tools/workstation/src/shared/contracts.ts`：补充 PC camera USB recovery 代理响应类型，明确该动作不发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：PC 页面打开后若 MJPEG status 明确为 UVC 传输/无首帧/USB 问题且不是页面独占，则自动执行一次固定 USB recovery，随后刷新 MJPEG URL 和 status；自动恢复状态只在切换小车地址时重置，避免 retry token 触发循环恢复。
- `pc-tools/workstation/test/App.test.ts`：新增 `/api/robot-control/camera/usb-recovery` fixture、fetch stub 和前端用例，覆盖“自动恢复一次、不发任何运动/建图/路线命令”的边界。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`：同步记录本轮图传恢复和 PC 大地图 / ROS2 配套工具口径。

## 验证结果

- `npm test -- test/App.test.ts -t "auto runs fixed USB recovery" --run`：通过，1 test OK / 239 skipped。
- 现场独占取帧复查：停止 `trashbot-local-webrtc-camera.service` 后，`v4l2-ctl`、`ffmpeg`、`gst-launch-1.0` 对 `/dev/video1` 的 MJPG/YUYV/current 格式仍 0 字节超时；恢复服务后 8088 active。
- 现场 PC recovery 读回：`POST /api/robot-control/camera/usb-recovery` 返回 `status=streamon_failed`、`frame_observed=false`、`usb_video_speed=480M`、`usb_high_speed_observed=true`、`stream_failure_class=high_speed_zero_byte_no_frame`、`next_action=check_usb_cable_port_power_or_known_good_uvc`。
- 现场 MJPEG 复测：`GET /api/robot-control/camera/mjpeg` 返回 HTTP 502；随后 status 为 `source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_failure_reason=first_frame_total_timeout`、`source_usage_owner_count=0`、`exclusive_camera_claim=false`。
- 地图口径复核：PC 普通入口仍优先使用首页大地图和 `/map` 直达页；ROS2 配套为工程观察，RViz2 本地看 `/map`、`/scan`、TF、路径、定位和 costmap，Foxglove bridge 供远程浏览器观察，不替代 PC 简易控制台。

## 剩余风险

- 自动 USB recovery 已接入 PC 打开即用路径，但当前 DV20 真实设备在独占 V4L2/ffmpeg/gstreamer 下仍不输出首帧；剩余动作是检查摄像头输入、USB 线/接口/供电，或更换 known-good UVC。
- 本轮未重新跑完整 Nav2 route 或 delivery success；wheel raw `T=1001 L/R` 非零仍未证明。
