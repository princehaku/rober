# 相机共享 MJPEG 低带宽兜底

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 在通用相机 capture 尝试和共享 MJPEG 首帧尝试中新增 `MJPG@160x120@30` 与 `YUYV@160x120@20`。
  - 共享 MJPEG 顺序保持“先真实低带宽 path 取帧，再 default/index/CAP_V4L2 兜底”，避免只因分辨率过高而错过可显示首帧。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 增加低带宽 fallback 存在性和顺序断言，要求 160x120 尝试排在 `default@current` 之前。
- `docs/product/pc_tools_workstation.md`
  - 同步普通 PC 图传边界：共享 MJPEG 已尝试极小真帧，仍失败时继续归因到摄像头输入、USB 线/接口/供电或设备本体。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步建图与运动边界：相机首帧仍只阻塞实时图传和建图视觉验收，不阻塞低速自由移动、WASD 或图上路线发车前置。

硬件协议复核来源：`docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON 资料仍用于区分底盘运动证据；本轮相机改动不改变 WAVE ROVER `T=11/T=13/T=1001` 控制或反馈协议。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.scripts.test_local_webrtc_camera_smoke_health`，48 tests passed。
- 通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/tests/test_local_webrtc_camera_smoke.py`。
- 通过：已把更新后的 `onboard/scripts/local_webrtc_camera_smoke.py` 部署到上位机 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`，并重启 `trashbot-local-webrtc-camera.service`；服务 active，监听 `0.0.0.0:8088`。
- 通过：PC 7001 `GET /api/robot-control/camera/mjpeg/status` 返回的 attempts 摘要已包含 `MJPG@160x120@30(/dev/video1)` 与 `YUYV@160x120@20(/dev/video1)`。
- 未通过但已定位：PC 7001 `GET /api/robot-control/camera/mjpeg` 仍返回 `502` / `first_frame_total_timeout`；上位机直接 V4L2 STREAMON 仍 0 字节，camera recovery 返回 `status=streamon_failed`，当前 DV20 为 USB `480M`，owner_count 为 `0`，所以不是浏览器页面独占。
- 运动链路复核：PC 7001 低速 manual pulse 返回 `proxy_status=command_forwarded`、`base_command_mode=ros`、`command_result_ok=true`、`stop_result_ok=true`、`motion_signal_observed=true`；上位机 command log 记录 `/cmd_vel -> esp32_bridge -> HTTP -> WAVE ROVER` 的 vendor `T=11,L=255,R=255` 和 stop `T=11,L=0,R=0`。

## 剩余风险

- “PC 实时图传可见”仍未完成：当前摄像头源没有输出真实视频 buffer，需要现场检查摄像头输入、USB 线/接口/供电，或换 known-good UVC 后执行 `POST /api/robot-control/camera/first-frame/probe`、`GET /api/robot-control/camera/mjpeg/status` 和 `POST /api/robot-control/camera/usb-recovery` 复测。
- `T=1001` wheel raw L/R 仍未证明非零；PC WASD/低速手控已有命令到达和 IMU 运动信号证据，但不能把它升级成 wheel raw 非零、完整 Nav2 路线执行或 delivery success。
- 本轮没有修改 PC 地图布局代码；地图太小的当前有效处理仍是 PC 首页大地图和 `/map` 直达页，ROS2 配套 RViz2/Foxglove 只作为工程观察。
