# 2026-06-28 21:10 camera MJPEG native FPS first frame

sprint_type: micro

## 实际改动

- 修改 `onboard/scripts/local_webrtc_camera_smoke.py`：共享 MJPEG 首帧 9 秒窗口内，优先尝试现场 DV20 UVC 枚举支持的 `MJPG@640x480@30`，再试 `YUYV@640x480@22` 和 `default@current`，最后保留配置值 `MJPG@640x480@15` 作为兼容兜底。
- 修改 `onboard/tests/test_local_webrtc_camera_smoke.py`：锁定共享 MJPEG 尝试顺序，避免回退到不支持的 15fps 优先。
- 更新 `docs/product/pc_tools_workstation.md`：记录 native-fps 优先、部署验证和只读边界。

硬件资料入口已复读 `docs/vendor/VENDOR_INDEX.md`。本轮只涉及 UVC 视频采集尝试顺序；未改 WAVE ROVER UART、底盘协议、引脚、电压或运动控制。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`，结果 `27 tests OK`。
- 通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`。
- 通过：同步到 `root@192.168.1.11:37878:/root/rober/onboard/scripts/local_webrtc_camera_smoke.py` 后，上车端 `python3 -m py_compile /root/rober/onboard/scripts/local_webrtc_camera_smoke.py`。
- 通过：重启 `trashbot-local-webrtc-camera.service`，服务 active，启动参数仍为 `--host 0.0.0.0 --port 8088 --video-source auto --width 640 --height 480 --fps 15`。
- 通过：PC 7001 只读请求 `/api/robot-control/camera/mjpeg` 返回 HTTP 502 JSON `first_frame_total_timeout`，安全字段 `safe_to_control=false`、`robot_control_executed=false`。
- 通过：上车端 `/api/camera/health` 显示 `first_frame_format_attempts=[MJPG@640x480@30,YUYV@640x480@22,default@current]`、`source_usage.status=not_in_use`、`owner_count=0`、`source_diagnosis.status=uvc_no_frame_not_exclusive`。
- 通过：PC 7001 `/api/robot-control/camera/mjpeg/status` 返回 `client_count=0`、`upstream_active=false`、`shared_capture=true`、`exclusive_camera_claim=false`、`last_failure_reason=first_frame_total_timeout`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、`robot_control_executed=false`。

## 剩余风险

- 真实摄像头画面仍未恢复；本轮把失败从“可能先试了不支持的 15fps”缩小为“设备原生 MJPG@30、YUYV@22 和 default 都没有首帧”。下一步仍是检查 DV20 输入源、USB 线/供电、采集卡状态，或更换 known-good UVC 复测。
- 本轮没有执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；完整路线执行、wheel raw L/R 非零和 delivery success 仍待现场安全确认后实车验证。
