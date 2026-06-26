# Camera First-Frame Modes WYSIWYG

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 8088 相机 smoke 首帧探测从粗粒度 `MJPG/YUYV/default` 扩展为具体模式：
    `MJPG@640x480@15`、`MJPG@640x480@30`、`YUYV@640x480@15`、`YUYV@640x480@22`、
    `YUYV@320x240@20`、`default@current`。
  - `default@current` 不写任何 OpenCV capture 参数，用内核当前协商模式兜底，避免强设不兼容格式时误判摄像头坏。
  - `/api/camera/health` 增加选中设备名、UVC/USB 标记、v4l2 支持格式摘要，方便 PC 首屏解释“不是页面独占”。
- `pc-tools/workstation`
  - Robot Control summary 新增 `selected_name`、`selected_is_uvc_or_usb`、`selected_formats_summary`。
  - 普通相机失败提示保留简易风格：显示 `USB Composite Device: DV20 USB` 和“不是页面独占”，不在首屏暴露 `/dev/video1`。
  - 采集尝试摘要最多展示 6 条，能看到 `default@current 无首帧`。
- `onboard/tests/test_local_webrtc_camera_smoke.py`、`pc-tools/workstation/test/*`
  - 补齐 v4l2 格式摘要、首帧 fallback 顺序、PC summary 和普通 UI 文案测试。

## 验证结果

- `python3 onboard/tests/test_local_webrtc_camera_smoke.py`
  - 22 tests passed。
- `npm test -- catalog.test.ts --testNamePattern "camera|Camera|summary|MJPG|YUYV"`
  - 22 passed / 85 skipped。
- `npm test -- App.test.ts --testNamePattern "camera|实时画面|共享画面|MJPG|YUYV"`
  - 21 passed / 120 skipped。
- `npm run build`
  - 通过；保留既有 Vite chunk size warning。
- 远端上车部署：
  - `scp` 更新 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`。
  - `systemctl restart trashbot-local-webrtc-camera.service` 后服务 active，8088 进程参数仍为 `--host 0.0.0.0 --port 8088 --video-source auto --width 640 --height 480 --fps 15`。
- 现场只读验证：
  - `/api/camera/health` 显示选中 `USB Composite Device: DV20 USB`，`source_usage.status=not_in_use`、`owner_count=0`。
  - 六种首帧尝试全部返回 `capture_read_returned_false`，包括 `default@current`。
  - PC 7001 live summary 显示 `selected_name=USB Composite Device: DV20 USB`、支持格式摘要和
    `MJPG@640x480@15 无首帧；...；default@current 无首帧`。

## 剩余风险

- 本轮证明当前不是页面独占，也不是 PC 共享预览多开抢占；DV20 USB 设备能枚举但所有模式都无首帧。
- 真实画面仍未恢复，下一步应检查摄像头输入源、USB 供电/线材、或换一个 known-good UVC 摄像头对照。
- 本轮未修改 Nav2 自动驾驶和底盘运动链路；它们继续沿用前序 sprint 的雷达可降级/停止兜底策略。
