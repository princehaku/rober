# Micro Sprint: 摄像头 DV20 真实模式探针与上车部署

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`: `camera_probe_fallback_requests` 从粗粒度 MJPG/YUYV fallback 升级为按 DV20/UVC 实板枚举的离散模式尝试：`MJPG 640x480@30`、`MJPG 1280x720@30`、`MJPG 480x320@30`、`YUYV 640x480@22`、`YUYV 320x240@25/20`，避免 PC 首帧探针一直用不支持的默认 15fps。
- `onboard/scripts/upper_robot_api.py`: fallback attempt summary 增加 `fps`，PC/日志能直接看出每次尝试的真实采集模式。
- `onboard/scripts/local_webrtc_camera_smoke.py`: 相机服务首帧尝试矩阵同步补齐 DV20 离散模式，MJPG/YUYV 都按板端枚举值尝试后再回退当前内核协商模式。
- `onboard/tests/test_upper_robot_api.py`、`onboard/tests/test_local_webrtc_camera_smoke.py`: 增加/更新测试，锁定真实 DV20 模式矩阵、fps 传递和 MJPG 多档失败后切换 YUYV 的释放行为。
- 已通过 SSH 同步 `upper_robot_api.py` 与 `local_webrtc_camera_smoke.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/`，并重启 `trashbot-local-webrtc-camera.service`、`trashbot-upper-robot-api.service`，两者均为 `active`。

## 验证结果

- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/local_webrtc_camera_smoke.py` 通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_local_webrtc_camera_smoke onboard.scripts.test_upper_robot_api_free_roam` 通过，82 tests OK。
- `git diff --check` 通过。
- 真机 `systemctl is-active trashbot-local-webrtc-camera.service trashbot-upper-robot-api.service` 输出两个 `active`。
- 真机 `/api/camera/first-frame/probe` 自动格式 fallback 已按 8 档真实模式尝试；全部 `open_ok=true` 但 `read_ok=false`，失败原因为 `capture_read_call_timeout`。
- 真机直接 `v4l2-ctl` 对 `/dev/video1` 的 MJPG/YUYV 多档抓帧输出 0 bytes；`ffmpeg` 也未产出帧。当前证据说明不是 PC 页面独占，摄像头设备枚举正常但底层没有输出视频帧。

## 剩余风险

- 摄像头真实画面仍未 ready；软件已经扩大格式矩阵并证明不是浏览器独占，下一步需要现场检查 DV20 摄像头输入、USB 供电、线材、或更换 known-good UVC 摄像头验证。
- Nav2 真机上已能完成 goal 并下发非零底盘命令，但轮速反馈仍为 0；后续仍需查 WAVE ROVER 电机使能、供电、底盘模式或反馈侧。
