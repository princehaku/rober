# PC 图传 DV20 0 帧复测

## sprint_type

micro

## 实际改动

- 继续按 PC 端总目标推进实时图传闭环，复测 8088 相机服务、8787 上位机 API 和本地 7001 PC 代理。
- 修正 PC 相机诊断文案：当真实设备名带 `(usb-...)` 总线尾巴时，后接“当前没人占用”会自动补空格，避免现场读到粘连文本。
- 更新 PC README 和产品文档，记录本轮 DV20 真实复测证据和剩余硬件动作边界。

## 验证结果

- `ssh root@192.168.1.11 -p 7878` 可连接，上位机为 Orange Pi Zero 3，`trashbot-local-webrtc-camera.service`、`trashbot-upper-robot-api.service`、雷达 lifecycle 和 ESP32 bridge 均为 active/running。
- 8088 `/health` 与 `/devices` 显示 DV20 `/dev/video1` 是唯一正分 `Video Capture` 候选，`/dev/video2` 是 metadata，USB 视频拓扑为 `480M`，当前无人占用。
- 7001 共享 MJPEG 复测返回 HTTP 502 JSON：`error=ffmpeg_mjpeg_first_frame_unreadable`，未读到 JPEG SOI。
- 7001 USB recovery 已执行相机服务 stop/start、USB reauthorize、audio unbind/rebind、autosuspend 关闭和 10 个 V4L2 控制项复位；返回 `status=streamon_success_zero_byte_no_frame`、`frame_observed=false`、`usb_video_speed=480M`、`streamon_success_observed=true`、`zero_byte_no_frame_observed=true`、`software_capture_exhausted=true`、`known_good_uvc_required=true`、`camera_input_signal_check_required=true`。
- 7001 deep first-frame probe 返回 `status=first_frame_timeout`、`backend_smoke_status=backend_no_frame_observed`、`backend_attempts=11`、`backend_userptr_attempt_count=2`、`backend_userptr_frame_observed=false`、`software_capture_exhausted=true`。
- live-summary 当前返回 `camera_current_visible=false`、`camera_shared_preview_everyone_can_join=true`、`camera_input_signal_check_required=true`、`known_good_uvc_required=true`、`software_capture_exhausted=true`，同时地图、路线、雷达点仍可见，整体 `status=ready_for_motion`。
- `npm test -- test/robotControlSummary.test.ts --run` 通过：1 个文件、18 个测试通过。

## 剩余风险

- PC 实时图传仍未完成：DV20 可以枚举和 STREAMON，但 kernel/V4L2/OpenCV/ffmpeg 均没有拿到任何 video buffer。当前已排除 PC 页面独占、低速 USB、V4L2 控制漂移、mmap/userptr/no-query 和 ffmpeg 路径。
- 下一步需要现场处理摄像头输入信号、视频线、接口、供电或换 known-good UVC 后复测；软件不能在无真实帧时伪造“实时图传成功”。
- WAVE ROVER vendor wheel raw L/R 非零闭环仍未证明；PC WASD 命令 raw 与 IMU 运动信号已证明，但 `T=1001` wheel raw 仍不是完成状态。
