# Micro Sprint: 共享摄像头预览与自由移动/Nav2 诊断

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`: 新增 `SharedCameraMjpegRelay`，把 `/api/camera/mjpeg` 从每个浏览器各自直连 camera service 改为上位机内存共享 MJPEG relay。多个 PC/浏览器进入预览时复用同一条上游流，减少 `/dev/video*` 独占或多开抢占造成的黑屏/无帧。
- `onboard/tests/test_upper_robot_api.py`: 新增共享 MJPEG relay 单元测试，证明两个客户端注册时只启动一条上游任务，并且两个客户端都收到同一真实 JPEG part。
- 复核现有自由移动链路：`/api/free-roam/autonomy/start` 只要求 `confirm_operator_safety`，雷达/相机缺口只降级 `mapping_readiness`，不会阻止低速移动；PC start 请求会发送 `confirm_operator_safety: true`，仅在建图质量 ready 时发送 `confirm_mapping_active: true`。
- 复核真机 Nav2 证据：`/api/nav2/goal/execution/latest` 显示 NavigateToPose 已 accepted，`base_command_summary.nonzero_command_observed=true`，最新命令包含 `{"T":11,"L":90,"R":-90}`；但 `base_feedback_summary.nonzero_sample_count=0`，`wheel_feedback_lr_nonzero_proven=false`。当前软件链路已走到非零底盘命令，下一级问题集中在底盘执行/电机使能/供电/模式或反馈侧。

## 验证结果

- `python3 -m py_compile onboard/scripts/upper_robot_api.py` 通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_shared_camera_mjpeg_relay_broadcasts_one_upstream_to_multiple_clients onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_free_roam_readiness_allows_optional_camera_and_stale_radar_for_motion` 通过，2 tests OK。

## 剩余风险

- 共享 relay 降低多人预览抢占风险，但真实 `/dev/video1` 仍需上车重启服务后用浏览器确认连续帧。
- 自动驾驶已证明非零命令下发，但轮速反馈仍为 0；下一轮需要继续查 WAVE ROVER 电机使能/底盘模式/供电或串口反馈，不应再把雷达作为主要阻塞。
