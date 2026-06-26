# Camera UVC 内核无帧诊断增强

## Sprint 类型

sprint_type: micro

## 实际改动

- `onboard/scripts/camera_first_frame_probe.py` 的 `--include-backend-smoke` 增加更明确的底层取帧状态：
  `no_frame_timeout`、`frame_observed`、`no_kernel_frame_observed`、0 字节输出、JPEG SOI 检查、
  `v4l2 --all` 和 `--list-formats-ext` 摘要。
- 后端矩阵结果继续写入 `safe_to_control=false`、`robot_control_executed=false`、
  `sends_motion_commands=false`，确保相机诊断不会解锁底盘或伪造建图 ready。
- `onboard/tests/test_camera_first_frame_probe.py` 增加 no-hardware 单元测试，覆盖 v4l2 超时 0 字节、
  JPEG 首帧证据和后端矩阵安全字段。
- `docs/vision/board_camera_publisher.md` 记录 2026-06-27 实板证据：camera service 已 active，
  `/dev/video1` 是 DV20 UVC capture，但 `v4l2-ctl --stream-mmap` MJPG/YUYV 均超时且 0 字节。

## 验证结果

- 已通过：`python3 -m unittest onboard.tests.test_camera_first_frame_probe`
- 已通过：`python3 -m unittest onboard.tests.test_camera_first_frame_probe onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_camera_probe_parses_subprocess_json_without_control_enable`
- 已通过：`python3 onboard/scripts/camera_first_frame_probe.py --device /dev/rober-missing-video --timeout-s 0.01 --read-call-timeout-s 0.01 --include-backend-smoke`
  本地缺 `cv2` 时返回 `status=dependency_missing`，并保持 `safe_to_control=false`、`sends_motion_commands=false`。
- 已同步上位机：`scp onboard/scripts/camera_first_frame_probe.py root@192.168.1.11:/root/rober/onboard/scripts/camera_first_frame_probe.py`
  后确认脚本包含 `BACKEND_INFO_TIMEOUT_S`、`jpeg_soi_observed`、`no_kernel_frame_observed`。
- 已通过实板探针：
  `ssh root@192.168.1.11 -p 37878 'timeout 60 python3 /root/rober/onboard/scripts/camera_first_frame_probe.py --device /dev/video1 --timeout-s 0.5 --read-call-timeout-s 0.5 --include-backend-smoke'`
  返回 `open_ok=true`、`status=first_frame_timeout`、`failure_reason=capture_read_call_timeout`；
  backend smoke 返回 `overall_status=no_kernel_frame_observed`、`failure_reason=v4l2_stream_timeout_no_bytes`、
  `no_frame_timeout_count=4`，四个后端 attempt 输出均为 `output_bytes=0`。
- 已通过：本地代码路径检查确认本轮没有改 Clash/proxy 配置，没有改 PC Node 端口，没有发送 `/cmd_vel`。

## 剩余风险

- 真实上位机 `/dev/video1` 仍未产出可见帧；当前结论是 UVC/kernel streaming no-frame，不是 PC 多浏览器独占。
- 本轮没有替换 DV20、USB 线、供电或摄像头输入源；现场仍需用 known-good UVC 或硬件复查确认根因。
- 自动驾驶/自由移动链路本轮未继续改动；前序提交已处理“自由移动不依赖雷达”和 Nav2/IMU 运动证据展示，但真实整路线仍需要硬件侧继续验证。
