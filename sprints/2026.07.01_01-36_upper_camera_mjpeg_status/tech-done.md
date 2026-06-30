# 上车 MJPEG 状态直连端点

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py` 新增只读 `GET /api/camera/mjpeg/status`，汇总 8088 `/health` 与 8787 共享 MJPEG relay snapshot。
- 新端点固定声明 `exclusive_camera_claim=false`、`shared_capture=true`、`opens_camera_device=false`、`starts_camera_mjpeg_stream=false`、`robot_control_executed=false`、`safe_to_control=false`，避免状态读取误触发摄像头或运动控制。
- `onboard/tests/test_upper_robot_api.py` 新增 MJPEG 状态 payload 与 aiohttp GET 路由注册测试，防止 8787 直连再次退回 405/缺路由。

## 验证结果

- 通过：`python3 -m py_compile onboard/scripts/upper_robot_api.py`
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api`，结果 `Ran 91 tests in 0.241s`，`OK (skipped=1)`。
- 通过：部署到 `root@192.168.1.11:37878`，重启 `trashbot-upper-robot-api.service` 后服务为 `active`，上车 `python3 -m py_compile /root/rober/onboard/scripts/upper_robot_api.py` 通过。
- 通过：上车只读读取 `GET http://127.0.0.1:8787/api/camera/mjpeg/status` 返回 HTTP 200，`status=source_first_frame_failed`、`preview_visible_status=not_visible_source_first_frame_failed`、`exclusive_camera_claim=false`、`opens_camera_device=false`、`starts_camera_mjpeg_stream=false`、`robot_control_executed=false`、`safe_to_control=false`。
- 通过：本机 PC `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 HTTP 200，仍显示相机 `source_first_frame_failed` 且 `shared_preview_exclusive_camera_claim=false`。

## 剩余风险

- 本改动解决 8787 直连状态端点缺失，不修复 DV20 UVC 当前无首帧问题；真实画面仍需现场检查 USB、摄像头输入、供电或换 known-good UVC 复测。
- 本轮未发送任何运动命令，也未主动拉起 MJPEG 流；只读状态无法证明画面像素已经可见。
