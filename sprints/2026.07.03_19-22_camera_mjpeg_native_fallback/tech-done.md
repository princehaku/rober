# 2026-07-03 19:22 Camera MJPEG Native Fallback

## sprint_type

micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 共享 MJPEG 首屏首帧矩阵补入 DV20 当前 native 模式 `MJPG@1280x720@30`。
  - 单次首帧尝试从 `0.75s` 收紧到 `0.6s`，让 `640 MJPG -> 1280 native MJPG -> 480 MJPG -> 320 YUYV -> 160 MJPG -> 160 YUYV` 六个关键模式能在主预算内跑到。
  - 注释继续明确该服务只读 camera，不触发底盘、Nav2、键盘、自由移动、delivery、stop 或 `/cmd_vel`。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 更新 MJPEG fallback 顺序和预算断言，锁住 native 1280x720 必须早于 default/current 和低带宽末级兜底。
- `docs/product/pc_tools_workstation.md`
  - 同步记录本轮上车部署、实测结果和剩余相机风险。

## 验证结果

- `python -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.scripts.test_local_webrtc_camera_smoke_health`
  - 通过：`Ran 48 tests in 16.636s`，`OK`。
- `python -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/tests/test_local_webrtc_camera_smoke.py`
  - 通过：无输出。
- 上车部署
  - `scp -P 7878 onboard/scripts/local_webrtc_camera_smoke.py root@192.168.1.11:/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`
  - `systemctl restart trashbot-local-webrtc-camera.service`
  - 服务恢复 `active`，监听 `0.0.0.0:8088`。
- 真实 MJPEG 触发复测
  - `GET http://192.168.1.11:8088/api/camera/mjpeg` 返回 HTTP `503`，结构化 body 包含：
    - `MJPG@640x480@30(/dev/video1)` 无首帧
    - `MJPG@1280x720@30(/dev/video1)` 无首帧
    - `MJPG@480x320@30(/dev/video1)` 无首帧
    - `YUYV@320x240@25(/dev/video1)` 无首帧
    - `MJPG@160x120@30(/dev/video1)` 无首帧
    - `YUYV@160x120@20(/dev/video1)` 无首帧
- PC 7001 camera status
  - `status=source_first_frame_failed`
  - `source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `selected_path=/dev/video1`
  - `camera_usb_speed=480M`
  - `source_usage_owner_count=0`
  - `camera_hardware_action_required=true`
  - `camera_hardware_action_label=检查摄像头输入/供电后复测`
- USB recovery 复测
  - `POST /api/robot-control/camera/usb-recovery` 返回 `status=streamon_failed`、`failure_reason=high_speed_zero_byte_no_frame`、`usb_video_speed=480M`。
  - 回包固定 `sends_motion_when_clicked=false`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`robot_control_executed=false`。
- 上位机服务状态
  - `trashbot-local-webrtc-camera.service active`
  - `0.0.0.0:8088` 正常监听。

## 剩余风险

- 实时图传仍未恢复真实帧；本轮已经排除“共享 MJPEG 没试 native 当前模式”和“服务没重启/页面独占”两类软件问题。
- 当前 DV20 是 USB `480M` 且无人占用，但所有 MJPG/YUYV/native/低带宽模式仍无首帧，USB recovery 仍 `high_speed_zero_byte_no_frame`。剩余动作需要现场检查摄像头输入/供电、USB 线/接口，或换 known-good UVC 后再复测。
- 本轮未改变 WASD、Nav2、delivery 逻辑；`delivery_success=false` 仍未闭环。
- `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/` 下两个旧 DOM smoke artifact 仍是历史脏文件，本轮未 stage、未提交。
