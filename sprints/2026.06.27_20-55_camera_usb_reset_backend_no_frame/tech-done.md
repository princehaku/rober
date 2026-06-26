# 2026.06.27 20:55 camera USB reset backend no-frame

sprint_type: micro

## 实际改动

- 更新 `docs/product/pc_tools_workstation.md`：补充 USB 重新枚举后 `/mjpeg` 仍 503、OpenCV 六种格式仍无首帧、backend smoke 仍无帧的 PC 侧 WYSIWYG 结论。
- 更新 `docs/vision/board_camera_publisher.md`：记录 `v4l2-ctl`、`ffmpeg`、USB unbind/bind、8088 MJPEG 和 8787 first-frame probe 的真实复测结果。

## 验证结果

- SSH 到 `root@192.168.1.11 -p 37878` 成功。
- `v4l2-ctl` 对 `/dev/video1` 的 MJPG/YUYV 采样均为 0 字节。
- `ffmpeg` 对 MJPG/YUYV 均未写出 JPEG。
- 对 USB 设备 `3-1` 执行 unbind/bind 后，DV20 重新枚举，`/dev/video1` 重新出现，camera service active。
- reset 后 `GET http://127.0.0.1:8088/mjpeg` 返回 HTTP 503，六种格式均 `capture_read_returned_false`。
- reset 后 `POST http://127.0.0.1:8787/api/camera/first-frame/probe` with `include_backend_smoke=true` 返回 `backend_no_frame_observed`，四个后端尝试均 timeout 且 `output_bytes=0`。

## 剩余风险

- 真实画面仍不可见；当前需要检查 DV20 输入源、采集卡模式、USB 线/供电或更换 known-good UVC。
- 本轮不改 PC 简易界面、不造假帧、不解锁建图 ready；摄像头和雷达都 ready 后才能按建图验收的 gate 继续保持。
