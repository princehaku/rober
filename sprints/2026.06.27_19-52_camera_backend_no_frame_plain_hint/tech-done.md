# Camera Backend No-Frame Plain Hint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通实时画面卡在 summary 已带 `first_frame_probe_backend_smoke_status=backend_no_frame_observed` 时，优先显示“OpenCV/V4L2 后端尝试 N 种方式也没有取到视频帧”。
  - 刷新页面后只剩 summary overlay，也不会退回泛化的 UVC 无帧文案，避免用户误以为只是浏览器页面独占或 WebRTC 问题。
  - 当前事实行同步显示 `OpenCV/V4L2 4 种方式也没有取到视频帧`，保持画面所见即所得。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 live not-in-use camera failure 回归：summary 带后端无帧证据时，普通首屏和 WYSIWYG 状态必须显示 OpenCV/V4L2 多方式无帧。

## 实板复核

- 已按 `docs/vendor/VENDOR_INDEX.md` 的硬件事实入口复核；本轮未修改 WAVE ROVER、UART、底盘 JSON 或运动配置。
- SSH 目标：`root@192.168.1.11 -p 37878`。
- 当前实板只读/短超时证据：
  - `trashbot-local-webrtc-camera.service=active`，8088 camera service 和 8787 upper API 均在监听。
  - `fuser -v /dev/video1 /dev/video2` 无其它占用者。
  - `/dev/video1` 是 `USB Composite Device: DV20 USB` 的 Video Capture 节点，`/dev/video2` 是 metadata 节点。
  - OpenCV `/dev/video1` 与 index `1` 都能 open，但 3 秒窗口没有读到帧；`/dev/video2` 不能打开为图像源。
  - `v4l2-ctl --stream-mmap` 8 秒超时，输出文件 0 字节。
  - PC probe `backendSmoke=1` 返回 `probe_failed`、`failure_reason=capture_read_call_timeout`、`backend_smoke_status=backend_no_frame_observed`、`backend_attempts=4`。

## 验证结果

- `npm test -- test/App.test.ts`
  - 通过：`177 passed`。

## 剩余风险

- 本轮没有修复 DV20 真实无帧；结论仍是硬件/输入/USB/供电或换 known-good UVC 复测。
- 未发送真实自由移动、Nav2 路线执行或底盘手控命令；运动验证仍需要现场明确安全确认。
- 只改 PC 普通界面的失败证据保真，不改变 camera service、WebRTC 或 MJPEG 取帧策略。
