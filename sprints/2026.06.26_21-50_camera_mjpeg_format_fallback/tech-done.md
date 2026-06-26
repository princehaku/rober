# Camera MJPEG Format Fallback

sprint_type: micro

## 实际改动

- 上车 `local_webrtc_camera_smoke.py` 的共享 camera capture 新增首帧 warmup 读取，避免 UVC 刚打开时一次 false 直接失败。
- WebRTC offer 和 MJPEG fallback 的首帧路径新增固定格式 fallback：`MJPG -> YUYV -> default`。
- 每个格式候选都必须读到真实首帧才成功；失败会释放当前 capture 再尝试下一个格式，不发送黑帧或占位图。
- 失败响应新增 `first_frame_format_attempts`，现场可直接看到每个格式的失败原因。
- 补充 `onboard/tests/test_local_webrtc_camera_smoke.py` 单元测试，覆盖 false-frame warmup 和 MJPG 失败后 YUYV 成功。
- 同步更新 `docs/hardware/board_sensor_stack_smoke.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`
  - `Ran 19 tests`
  - `OK`
- 通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/tests/test_local_webrtc_camera_smoke.py`
- 已部署到真实上位机 `root@192.168.1.11 -p 37878`：
  - `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`
  - camera service 重启为 PID `146741`
- 真实上位机 smoke：
  - `GET http://192.168.1.11:8787/api/camera/mjpeg` 返回 HTTP `502`，远端 camera service 为 HTTP `503`。
  - `first_frame_format_attempts` 显示 `MJPG`、`YUYV`、`default` 三个候选全部 `first_frame_unreadable/capture_read_returned_false`。
  - `/api/camera/health` 返回 `source_usage.status=not_in_use`、`owner_count=0`，不是 PC 或其它进程独占。
  - 固定 `v4l2-ctl` 后端 smoke 中，MJPG 和 YUYV 采样文件均为 `0` 字节。

## 剩余风险

- 本轮修复了 camera service 格式 fallback 和失败可解释性，但真实 `/dev/video1` 仍没有输出视频帧，实时画面仍不可见。
- 当前剩余风险更接近摄像头输入、USB 线/供电、采集设备模式或摄像头本体问题；建议下一轮接 known-good UVC 摄像头或重新插拔/换线复测。
- 本轮没有调用 manual、Nav2、delivery、free-roam start/stop 或 `/cmd_vel`。
