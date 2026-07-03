# Tech Done

sprint_type: micro

## 实际改动

- 本轮未改产品代码，执行真实上位机相机恢复与诊断，确认 PC 实时图传缺口的根因不在浏览器独占或 PC relay。
- 更新 `docs/product/pc_free_roam_mapping_design.md`，记录 2026-07-03 相机 USB full-speed 复查、已尝试恢复动作和下一步硬件动作。

## 验证结果

- PC `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787`：
  - `shared_preview_everyone_can_join=true`
  - `source_usage_scope=free`
  - `source_usage_not_exclusive=true`
  - `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `camera_usb_speed=12M`
  - `hardware_action_required=true`
  - `first_frame_failure_reason=first_frame_total_timeout`
- 上位机 `lsusb -t`：摄像头 `USB Composite Device: DV20 USB` 位于 `Bus 06` OHCI `12M` full-speed；同机存在多个 `480M` root hub，但当前摄像头未挂到高速链路。
- 上位机 `v4l2-ctl --list-formats-ext -d /dev/video1`：`/dev/video1` 是 UVC 视频节点，支持 `MJPG 1280x720/640x480/480x320/1920x1080 @30` 和 `YUYV 640x480@22、320x240@25/20`；`/dev/video2` 是 metadata，`/dev/video0` 是 cedrus 解码器。
- 直接取帧失败，排除了 PC relay 和 8088 服务层：
  - `v4l2-ctl ... MJPG 640x480`：`VIDIOC_STREAMON returned -1 (Input/output error)`，输出文件 0 字节。
  - `v4l2-ctl ... MJPG 480x320`：`VIDIOC_STREAMON returned -1 (Input/output error)`，输出文件 0 字节。
  - `v4l2-ctl ... YUYV 320x240`：`VIDIOC_STREAMON returned -1 (Input/output error)`，输出文件 0 字节。
  - `ffmpeg ... mjpeg 480x320`：`ioctl(VIDIOC_STREAMON): Input/output error`。
  - `ffmpeg ... yuyv422 320x240`：`ioctl(VIDIOC_STREAMON): Input/output error`。
- 已尝试远端软恢复：
  - stop/start `trashbot-local-webrtc-camera.service`
  - `/sys/bus/usb/devices/6-1/authorized` USB reset
  - 临时解绑 `snd-usb-audio` 的 `6-1:1.2` / `6-1:1.3` 后复测视频，再绑定恢复
  - 结果仍为 `12M` full-speed 与 `STREAMON` I/O error。
- `curl /api/robot-control/camera/mjpeg`：HTTP 502，`time_total=0.152089`，证明 PC 共享 MJPEG endpoint 能快速返回上游真实失败，不是页面等待或独占卡死。
- 回归确认地图未受影响：`GET /api/robot-control/map/preview` 返回 `proxy_status=preview_forwarded`、`path_preview_point_count=18`、`route_target_visible=true`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_point_count=135`。

## 剩余风险

- 实时图传仍未达成。当前证据显示必须进行物理动作：把摄像头换到 480M 高速 USB 口/线，或换带供电 USB Hub，再复跑 `/api/robot-control/camera/first-frame/probe` 和 `/api/robot-control/camera/mjpeg/status`。
- PC 共享预览机制已经能让多个页面接入同一条上游流；但在 UVC 源无法 STREAMON 前，页面不会有真实实时画面。
- 音频接口解绑测试已恢复绑定；未留下故意的运行时硬件配置变更。
