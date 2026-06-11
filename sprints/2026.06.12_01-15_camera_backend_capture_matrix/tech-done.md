# Camera Backend Capture Matrix

sprint_type: micro

## 目标

继续推进真实上车 evidence capture，不使用 subagent。当前 PC 实时图传的 blocker 是
DV20 `/dev/video1` 首帧 timeout。本轮目标是判断问题是否只发生在 OpenCV/WebRTC，还是
底层 V4L2/ffmpeg 也无法拿到帧，并把该诊断接入 PC 高级诊断。

本轮只触碰 camera/V4L2 只读采集路径，不改 WAVE ROVER UART，不调用 `/api/base/manual`，
不发布 `/cmd_vel`，不打开 `/dev/ttyS5`。硬件事实入口已读 `docs/vendor/VENDOR_INDEX.md`。

## 实际改动

- `onboard/scripts/camera_first_frame_probe.py`
  - 新增 `--include-backend-smoke`。
  - OpenCV 首帧失败后，可额外运行固定白名单后端矩阵：
    `v4l2-ctl MJPG`、`v4l2-ctl YUYV`、`ffmpeg mjpeg`、`ffmpeg yuyv422`。
  - 输出 `backend_smoke.status`、`frame_observed`、每次尝试的 returncode、timeout、
    stderr preview 和 output bytes。
- `onboard/scripts/upper_robot_api.py`
  - `POST /api/camera/first-frame/probe` 白名单透传 `include_backend_smoke=true`。
  - backend smoke 场景加长 helper timeout，避免 PC/upper wrapper 提前打断。
- `pc-tools/workstation/src/server/index.ts`
  - PC 高级首帧探针固定请求 `include_backend_smoke=true`，timeout 增至 60s。
  - proxy response 增加 `backend_smoke_status`、`backend_frame_observed`、
    `backend_attempts` 短字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 默认关闭的高级诊断显示 backend smoke 摘要；普通首屏不变。
- `docs/vision/board_camera_publisher.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 backend matrix 结论。

## 验证结果

- 本地 Python 测试：
  - `python3 -m unittest onboard.tests.test_camera_first_frame_probe onboard.tests.test_upper_robot_api`
  - 结果：37 tests OK。
- 本地语法检查：
  - `python3 -m py_compile onboard/scripts/camera_first_frame_probe.py onboard/scripts/upper_robot_api.py onboard/tests/test_camera_first_frame_probe.py onboard/tests/test_upper_robot_api.py`
  - 结果：通过。
- PC App 单测：
  - `npm run test -- App.test.ts`
  - 结果：17 tests passed。
- 上位机部署：
  - scp `camera_first_frame_probe.py`、`upper_robot_api.py` 到
    `root@192.168.1.11:/root/rober/onboard/scripts/`。
  - 远端 py_compile 通过；`trashbot-upper-robot-api.service` 重启后 active。
- 实板 backend matrix：
  - artifact：`artifacts/01_board_camera_backend_matrix.log`
  - 停止 camera service 后，`/dev/video0/1/2` 和 `/dev/ttyS5` 均无 holder。
  - `v4l2-ctl --list-devices`：`/dev/video1` 仍是 DV20 USB Video Capture。
  - `v4l2-ctl --all -d /dev/video1`：input ok，支持 MJPG/YUYV。
  - `v4l2-ctl` default/MJPG/YUYV 采集输出均为 0 bytes。
  - `ffmpeg` mjpeg/yuyv422 采集均无 frame 写出。
  - 测试结束后 camera service 恢复 active。
- 上位机 API backend smoke：
  - artifact：`artifacts/02_upper_camera_probe_backend_smoke.json`
  - `status=first_frame_timeout`、`open_ok=true`、`read_ok=false`、
    `failure_reason=capture_read_call_timeout`。
  - `backend_smoke.status=backend_no_frame_observed`、`frame_observed=false`。
  - 四个后端尝试 output bytes 均为 0。
- PC proxy backend smoke：
  - artifact：`artifacts/03_pc_proxy_camera_probe_backend_smoke.json`
  - `remote_http_status=503`、`status=first_frame_timeout`。
  - `probe_key_values.backend_smoke_status=backend_no_frame_observed`、
    `backend_frame_observed=false`、`backend_attempts=4`。
- 清场：
  - `trashbot-upper-robot-api.service=active`、`trashbot-local-webrtc-camera.service=active`。
  - `/dev/video0/1/2` 和 `/dev/ttyS5` 无 holder。

## 剩余风险

- 这轮证明了问题不只在 OpenCV/WebRTC：V4L2 和 ffmpeg 也拿不到 DV20 首帧。
- 实时图传可见内容仍未恢复；下一步需要现场检查 DV20 输入源、HDMI/USB 线缆、供电、
  采集卡状态，或更换 known-good UVC 后用同一高级按钮复测。
- 非 stop 运动 gate 仍缺 visible camera、外部视频、轮速反馈非零和 LiDAR motion delta。
