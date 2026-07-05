# PC Camera Relay Nested Failure Status

## sprint_type

micro

## 实际改动

- 修改 `onboard/scripts/upper_robot_api.py`：`/api/camera/mjpeg/status` 会读取 8787 共享 MJPEG relay 的 `last_error_payload.last_first_frame_error`，避免自动重试 cooldown 把真实无首帧降级成 `source_selected_not_probed`。
- 新增 `onboard/tests/test_upper_robot_api.py` 回归测试，覆盖 `mjpeg_auto_retry_cooldown_after_first_frame_failure` 包裹 `ffmpeg_mjpeg_first_frame_unreadable` 的场景。
- 部署更新后的 `upper_robot_api.py` 到 `root@192.168.1.11 -p 7878`，重启 `trashbot-upper-robot-api.service`；旧进程 SIGTERM 卡住后用 systemd SIGKILL 清理并重新 start。
- 更新 `docs/product/pc_tools_workstation.md` 和 `docs/vision/board_camera_publisher.md`，同步 8787/7001 相机状态口径和现场 USB/V4L2 复验结果。

## 验证结果

- 本地 `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_camera_mjpeg_status_uses_relay_nested_first_frame_failure_during_cooldown onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_shared_camera_mjpeg_relay_preserves_upstream_first_frame_error_body`：2 tests OK。
- 本地 `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py`：通过。
- 本地 `python3 -m unittest onboard.tests.test_upper_robot_api`：105 tests OK，1 skipped。
- 上位机 `python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py`：通过；`trashbot-upper-robot-api.service=active`。
- 停止 8088 后直连 `/dev/video1`：`MJPG@640x480@30` 与 `YUYV@320x240@25` 均 `VIDIOC_STREAMON returned 0 (Success)`，但 10 秒输出 0 字节；`ffmpeg -f v4l2` 也没有写出 JPEG。
- USB `3-1` reauthorize 并解绑 `3-1:1.2/3-1:1.3` audio 接口后，`/dev/video1` 重新枚举，直采仍 0 字节。
- 8787 `GET /api/camera/mjpeg/status` 顺序读回：`status=source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_failure_reason=ffmpeg_mjpeg_first_frame_unreadable`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_hardware_action_label=检查摄像头输入/供电后复测`，并显示 `MJPG@640x480@30`、`MJPG@1280x720@30`、`MJPG@480x320@30`、`YUYV@320x240@25`、`MJPG@160x120@30`、`YUYV@160x120@20` 无首帧摘要。
- PC 7001 `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 返回 `source_first_frame_failed`、`source_failure_reason=high_speed_zero_byte_no_frame`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、`camera_hardware_action_label=检查摄像头输入/供电后复测`，并透传多格式无首帧摘要。
- PC 7001 `live-summary` 仍为 `status=ready_for_motion`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`keyboard_ready=true`。

## 剩余风险

- 实时图传仍未恢复真实画面；当前已排除 PC 页面独占、8088 服务独占、USB 12M 低速和单一 OpenCV 格式问题，剩余风险集中在 DV20 输入信号、视频线/接口/供电、采集卡/摄像头本体或 known-good UVC 复测。
- `T=1001` wheel raw L/R 反馈仍未证明非零；本轮未改变底盘控制逻辑。
- `trashbot-upper-robot-api.service` 停止时旧进程仍可能因子进程等待导致 SIGTERM 慢退出；本轮只完成状态汇总修复，未重构服务 shutdown。
