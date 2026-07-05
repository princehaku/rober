# PC camera reset matrix and map/WASD revalidation

sprint_type: micro

## 实际改动

- 本轮不改产品代码；继续围绕 PC 端目标做真实上位机恢复和验证。
- 在上位机 `192.168.1.11:7878` 上执行相机低风险恢复：
  - 停止 `trashbot-local-webrtc-camera.service`。
  - 确认 `/dev/video1` 无 owner。
  - 将 UVC input 设回 `Input 1`，并复位 brightness/contrast/saturation/gamma/gain/power_line/white_balance/sharpness/backlight/auto_exposure 等控制项。
  - 对 USB `3-1` 执行 reauthorize，设备重新枚举为 Jieli `4c4a:4a55`，仍在 480M high-speed。
  - 重启 `trashbot-local-webrtc-camera.service`，服务恢复 active。
- 同步文档：
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
  - `docs/product/pc_tools_workstation.md`
  - `docs/product/pc_free_roam_mapping_design.md`
  - `pc-tools/README.md`

## 验证结果

- 相机设备事实：
  - `/dev/video1` 是 `USB Composite Device: DV20 USB` UVC capture。
  - `/dev/video2` 是 metadata capture。
  - `/dev/video0` 是 cedrus decoder，不是摄像头。
  - `/dev/video1` 支持 `MJPG` `1280x720/640x480/480x320/1920x1080` 和 `YUYV` `640x480/320x240`。
  - `lsusb -t` 显示 DV20 在 USB `480M` high-speed。
- 采帧矩阵：
  - `v4l2-ctl` mmap：`MJPG 640x480/1280x720/480x320`、`YUYV 320x240/640x480` 均 `0 bytes`。
  - `v4l2-ctl` userptr：同一组格式均 `0 bytes`。
  - `ffmpeg`：MJPG 报 EOF/无法得到实际像素帧，YUYV 能枚举 rawvideo 参数但 `frame=0`、输出为空。
  - 控制项复位前 `MJPG 640x480` 快采为 `0 bytes`；USB reauthorize 后 `YUYV 320x240` 快采仍为 `0 bytes`。
- PC 7001 复验：
  - first-frame probe 返回 `probe_total_timeout`、`frame_observed=false`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_hardware_action_label=检查摄像头输入/供电后复测`。
  - 雷达按固定只读链路刷新后，`radar_status=loaded`、当前雷达点 `101`。
  - live-summary 返回 `status=ready_for_motion`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`camera_current_visible=false`、`keyboard_motion_verified=true`、`keyboard_command_raw_lr_nonzero_proven=true`、`keyboard_stop_settled_after_pulse=true`。
  - PC manual forward/backward 均返回 `proxy_status=command_forwarded`、`command_raw_lr_nonzero_proven=true`、`motion_signal_observed=true`、`stop_result_ok=true`。

## 剩余风险

- 实时图传仍未完成：当前已经排除页面独占、PC relay、USB full-speed、CMA、单一 OpenCV backend、mmap/userptr 差异和 UVC 控制项异常；剩余指向 DV20 上游视频输入、视频线、USB 线/接口/供电、采集卡/摄像头本体，或需要换 known-good UVC 复测。
- 低速移动/WASD 可继续使用 command raw + stop + IMU 动作信号证明“能动”；但按 `docs/vendor/VENDOR_INDEX.md` 中 WAVE ROVER JSON 反馈字段，vendor `T=1001 L/R=0/0` 仍不能宣称 wheel raw L/R 非零或完整自动驾驶/delivery success 闭环完成。
