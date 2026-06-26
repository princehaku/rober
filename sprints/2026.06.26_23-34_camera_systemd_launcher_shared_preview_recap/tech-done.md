# Camera Systemd Launcher Shared Preview Recap

## sprint_type

micro

## 实际改动

- 新增 `onboard/scripts/local_webrtc_camera_smoke.sh`：把 8088 camera smoke 的 systemd 启动入口入仓，默认 `HOST=0.0.0.0`、`PORT=8088`、`ROBER_CAMERA_SOURCE=auto`，只启动 `local_webrtc_camera_smoke.py`，不触碰 ROS2、串口、Nav2 或底盘控制。
- 修改 `onboard/tests/test_local_webrtc_camera_smoke.py`：增加启动脚本合同测试，锁定默认绑定、auto 选源和 camera-only 安全边界。
- 更新 `docs/vision/board_camera_publisher.md`：记录真实上位机复查结论，当前看不到画面不是多客户端独占，而是 `/dev/video1` 首帧 `capture_read_returned_false`；同时记录 8088 当前由手工进程监听、systemd service inactive 的运行形态漂移。

## 真实上位机复查

- `GET http://192.168.1.11:8787/api/camera/health`：`source_readiness=first_frame_failed`、`source_failure_reason=capture_read_returned_false`、`last_successful_frame=null`。
- 同一 health 中 `source_usage.other_owner_count=0`，失败 MJPEG 后复查 `shared_captures={}`，没有观察到其它进程长期独占 `/dev/video1`。
- `GET http://192.168.1.11:8787/api/camera/mjpeg`：5 秒内未输出真实 JPEG，curl 超时。
- `ssh root@192.168.1.11 -p 37878 'systemctl is-active trashbot-local-webrtc-camera.service; ss -ltnp | grep :8088'`：`trashbot-local-webrtc-camera.service=inactive`，但 8088 由手工 `python3 scripts/local_webrtc_camera_smoke.py ...` 进程监听。

## 验证结果

- `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`：通过，`Ran 21 tests in 0.355s`，`OK`。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`：通过。
- `git diff --check`：通过。

## 剩余风险

- 本轮修复的是 camera service 启动入口可复现性，并记录真实阻塞点；还没有解决 DV20 `/dev/video1` 首帧输出失败。
- 尚未在远端停止手工 8088 进程并切回 systemd 管理；切换需要短暂中断 camera service，后续应在现场可接受时执行 `systemctl restart trashbot-local-webrtc-camera.service` 并复查。
