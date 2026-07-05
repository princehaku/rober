# Camera USB Power Policy Recovery

## sprint_type

micro

## 实际改动

- 修改 `onboard/scripts/camera_usb_recovery_smoke.py`：`set_usb_power_on()` 现在同时写目标 USB 设备和 root hub 的 `power/control=on`、`power/autosuspend=-1`、`power/autosuspend_delay_ms=-1`，并在 `power_actions` 中记录每项 before/after。
- 修改 `onboard/scripts/test_camera_usb_recovery_smoke.py`：新增 no-hardware 单元测试，锁定 autosuspend 关闭证据。
- 部署更新后的 `camera_usb_recovery_smoke.py` 到 `root@192.168.1.11 -p 7878`。
- 更新 `docs/product/pc_tools_workstation.md` 和 `docs/vision/board_camera_publisher.md`，同步本轮 USB power policy 复验结论。

## 验证结果

- `python3 onboard/scripts/test_camera_usb_recovery_smoke.py`：7 tests OK。
- `python3 -m unittest onboard.tests.test_camera_usb_recovery_smoke`：3 tests OK。
- `python3 -m py_compile onboard/scripts/camera_usb_recovery_smoke.py onboard/scripts/test_camera_usb_recovery_smoke.py onboard/tests/test_camera_usb_recovery_smoke.py`：通过。
- 本地与上位机 `/root/rober/onboard/scripts/camera_usb_recovery_smoke.py` SHA256 一致：`ea7f8b9314c6a83f9e7bb45d188e7035852bbacd35b4e4b779b7543698ef1bb5`。
- 上位机执行 `python3 scripts/camera_usb_recovery_smoke.py --device /dev/video1 --skip-service --skip-reauthorize --skip-audio-unbind`：`usb_device=3-1`、`usb_video_speed=480M`，`3-1` 与 `usb3` 的 `power/control=on`、`power/autosuspend=-1`、`power/autosuspend_delay_ms=-1` 均写入成功。
- 同次复验仍返回 `status=streamon_success_zero_byte_no_frame`，`YUYV@320x240@20` 与 `MJPG@480x320@30` 均无帧。

## 剩余风险

- 实时图传仍未恢复真实画面；autosuspend 已被排除为当前主要原因，剩余风险继续集中在 DV20 输入信号、视频线/接口/供电、采集卡/摄像头本体或 known-good UVC 复测。
- 本轮不改变 7001 地图、WASD 或 Nav2 控制逻辑；这些链路仍沿用上一轮 live-summary 验证结果。
