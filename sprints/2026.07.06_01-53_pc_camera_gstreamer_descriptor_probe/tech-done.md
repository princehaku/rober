# PC camera GStreamer and descriptor probe

sprint_type: micro

## 实际改动

- 本轮不改产品代码；继续围绕 PC 实时图传缺口做真实上位机排查。
- 在上位机 `192.168.1.11:7878` 读取 DV20 USB/UVC 描述符、media graph、GStreamer 采集路径和 PC 7001 当前运行态。
- 同步文档：
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
  - `docs/product/pc_tools_workstation.md`
  - `pc-tools/README.md`

## 验证结果

- `lsusb -v -d 4c4a:4a55` 确认 DV20 是 Jieli `USB Composite Device`，bus powered `400mA`，UVC 1.00。
- UVC 描述符显示：
  - VideoControl processing unit 有 `Descriptor too short` 警告。
  - 存在 vendor extension unit `{28f03370-6311-4a2e-ba2c-6890eb334016}`，`bNumControls=8`，但标准 `v4l2-ctl --list-ctrls-menus` 只暴露亮度、曝光、白平衡等普通控制项，没有可直接切输入源的标准控制。
  - VideoStreaming endpoint 是 EP4 IN，MJPG 与 YUYV 格式和分辨率仍可正常枚举。
- `media-ctl -p -d /dev/media1` 确认 graph 为 `Input 1 -> Processing 2 -> Extension 3 -> /dev/video1`，链路 enabled/immutable。
- GStreamer 直采结果：
  - `image/jpeg 640x480@30`：协商成功但输出 `0 bytes`。
  - `image/jpeg 1280x720@30`：协商成功但输出 `0 bytes`。
  - `video/x-raw,format=YUY2 320x240@25`：协商成功但输出 `0 bytes`。
  - `video/x-raw,format=YUY2 640x480@22`：协商成功但输出 `0 bytes`。
- PC 7001 复验：
  - `POST /api/robot-control/camera/first-frame/probe` 返回 `probe_total_timeout`、`frame_observed=false`、`source_diagnosis_status=uvc_no_frame_not_exclusive`。
  - 固定只读雷达刷新后，`live-summary` 返回 `status=ready_for_motion`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`camera_current_visible=false`、`keyboard_motion_verified=true`、`keyboard_command_raw_lr_nonzero_proven=true`、`keyboard_stop_settled_after_pulse=true`。

## 剩余风险

- 实时图传仍未完成。当前又排除了 GStreamer 路径，剩余更集中在 DV20 上游视频输入、视频线、USB 线/接口/供电、采集卡/摄像头本体，或者 vendor extension unit 里存在未公开的输入切换控制。短期最快验证仍是接入 known-good UVC 摄像头或确认 DV20 上游输入源真的在输出视频。
- PC 地图和 WASD 仍可用；雷达点本轮刷新后为当前可见，但点数随现场 scan 窗口变化，本轮读到 `9` 个点。
- wheel raw `T=1001 L/R=0/0` 仍不能宣称完整底盘反馈闭环，硬件协议口径继续采用 `docs/vendor/VENDOR_INDEX.md`。
