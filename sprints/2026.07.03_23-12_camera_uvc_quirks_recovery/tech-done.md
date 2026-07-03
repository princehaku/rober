# 2026.07.03 23:12 Camera UVC Quirks Recovery

## sprint_type

micro

## 实际改动

- `onboard/scripts/camera_usb_recovery_smoke.py`
  - 恢复脚本默认记录 `uvcvideo` 模块参数，并把 `quirks` 复位到 `0` 后再做 USB reauthorize 与 STREAMON smoke。
  - 回包新增 `uvc_quirks_before`、`uvc_quirks_after_reset`、`uvc_quirks_after` 和完整 `uvc_module_parameters_*` 证据。
  - 新增 `--skip-uvc-quirks-reset`，用于现场保守复测。
- `onboard/scripts/upper_robot_api.py`
  - `POST /api/camera/usb-recovery` 白名单 body 新增 `skip_uvc_quirks_reset`，只会翻译为固定脚本参数。
- `pc-tools/workstation/src/server/index.ts`
  - PC 固定代理 `POST /api/robot-control/camera/usb-recovery` 新增同名布尔白名单开关。
  - PC 顶层回包透出 UVC quirk 复位前后字段，便于现场脚本直接读证据。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐相机 USB 恢复代理的 UVC quirk 读回类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通相机复验 DOM 增加 `data-auto-usb-recovery-uvc-quirks-*` 只读字段；可见文案仍保持简易用户口径。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 PC body 清洗与 UVC quirk 顶层回包。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通相机复验 DOM 的 UVC quirk data 字段。
- 文档同步：
  - `pc-tools/README.md`
  - `docs/product/pc_tools_workstation.md`
  - `docs/product/pc_free_roam_mapping_design.md`
  - `docs/vision/board_camera_publisher.md`

## 验证结果

- `python3 -m unittest onboard/scripts/test_camera_usb_recovery_smoke.py`：通过，3 passed。
- `python3 -m py_compile onboard/scripts/camera_usb_recovery_smoke.py onboard/scripts/upper_robot_api.py`：通过。
- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "workstation camera USB recovery proxy only forwards the fixed recovery endpoint"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "auto runs fixed USB recovery once when shared MJPEG status reports UVC no-frame hardware action"`：通过，1 passed。
- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc` 均成功。
- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`：通过，190 passed。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts`：通过，240 passed。
- 部署验证：
  - 已只覆盖上位机 `/root/rober/onboard/scripts/camera_usb_recovery_smoke.py` 与 `/root/rober/onboard/scripts/upper_robot_api.py`，并重启 `trashbot-upper-robot-api.service`。
  - 上位机 `trashbot-upper-robot-api.service` 与 `trashbot-local-webrtc-camera.service` 均为 `active`。
  - 本机 PC Node 已重启，监听 `0.0.0.0:7001`。
- 现场恢复代理验证：
  - `POST http://127.0.0.1:7001/api/robot-control/camera/usb-recovery?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
    返回 `proxy_status=recovery_forwarded`、`status=streamon_failed`、`usb_video_speed=480M`、
    `stream_failure_class=high_speed_zero_byte_no_frame`、`uvc_quirks_before=0`、
    `uvc_quirks_after_reset=0`、`uvc_quirks_after=0`。
  - recovery payload 显示 `uvc_quirks_reset.ok=true`，`YUYV@320x240@20` 与
    `MJPG@480x320@30` 均 `bytes=0`。
  - 真实上位机先前同轮手动复核：`quirks=4294967295` 与复位 `quirks=0` 后，
    `MJPG@640x480`、`MJPG@1280x720`、`YUYV@320x240` 均 0 字节；服务恢复 active。
- 现场 PC 状态验证：
  - 触发共享 MJPEG 后，`/api/robot-control/camera/mjpeg/status` 为
    `source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、
    `first_frame_failure_reason=first_frame_total_timeout`、`exclusive_camera_claim=false`、
    `usb_speed=480M`、`camera_hardware_action_label=检查摄像头输入/供电后复测`。
  - radar no-motion refresh 后 summary 为 `map_preview_status=loaded`、`path_preview_point_count=18`、
    `route_target_visible=true`、`robot_pose_status=map_pose_observed`、
    `radar_overlay_status=loaded`、`radar_overlay_current_point_count=168`。
  - PC 固定 manual 前进/后退短脉冲均 `proxy_status=command_forwarded`、
    `base_command_mode=ros`、`feedback_mode=realtime`、`command_result_ok=true`、
    `stop_result_ok=true`、`motion_signal_observed=true`；stop 代理 `status=stopped`。
  - stop 后 summary 为 `keyboard_continuous_motion_verified=true`、
    `keyboard_stop_after_release=true`、`keyboard_wheel_lr_nonzero=false`。

## 剩余风险

- 相机仍无真实首帧；当前证据已排除页面独占、服务未重启、当前异常 UVC quirk、USB 12M 低速和常见格式遗漏，剩余是摄像头输入、USB 线/接口/供电或 DV20/采集设备本体复测。
- WAVE ROVER wheel raw L/R 非零仍未证明，实车 manual 回包仍是 `wheel_feedback_latest_raw_left/right=0/0`；本轮只证明命令转发、自动 stop 和 IMU/运动信号。
- 本轮未跑 Docker/Humble `colcon build`，因为改动集中在 PC Node/Vue、上车 HTTP 脚本和文档，未改 ROS2 package 构建面；已用 Python 编译、PC build、Vitest 和真实 8787/7001 现场验证覆盖本轮风险。
