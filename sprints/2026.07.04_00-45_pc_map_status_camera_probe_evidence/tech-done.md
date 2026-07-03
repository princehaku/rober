# PC map status and camera direct probe evidence

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 将 `readback_summary.map.status` 从直接复用底层 `map_proof_latest.status` 改为按当前 PC 地图 WYSIWYG 证据合成。
  - 当前地图、路线、小车位姿和雷达贴图都可见时返回 `loaded`；地图有缺层时返回 `partial`；未读到地图时才保留底层 proof 状态或 `not_loaded`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加回归断言，锁住完整地图/路线/位姿/雷达贴图为 `loaded`，图层不完整但已有地图时为 `partial`。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/vision/board_camera_publisher.md`
  - 同步记录本轮地图状态合同和 2026-07-04 00:44 CST 上车端 DV20 直接取帧证据。

## 验证结果

- 已在上车端停止 `trashbot-local-webrtc-camera.service` 后确认 `/dev/video1` 无其它 owner，并直接复测：
  - `v4l2-ctl MJPG@640x480@30 --stream-mmap`：8 秒超时，输出 0 字节。
  - `v4l2-ctl YUYV@320x240@25 --stream-mmap`：8 秒超时，输出 0 字节。
  - `ffmpeg -f v4l2 -input_format mjpeg -video_size 640x480`：8 秒内没有写出 JPEG。
  - 复测后已重启相机服务，`trashbot-local-webrtc-camera.service` 为 `active`。
- `npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts -t "map preview|current map|route target|radar overlay"`：通过，2 passed。
- `npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "radar overlay|map preview|route target"`：通过，5 passed。
- `npm --prefix pc-tools/workstation test -- --run`：通过，3 个 test file，447 passed。
- `npm --prefix pc-tools/workstation run build`：通过，仅保留 Vite 大 chunk warning。
- PC Node 已重启到 `0.0.0.0:7001`。
- Live 只读刷新后 `GET /api/robot-control/summary`：
  - `readback_summary.map.status=loaded`
  - `map_current_visible=true`
  - `path_current_visible=true`
  - `route_target_visible=true`
  - `robot_pose_status=map_pose_observed`
  - `radar_overlay_status=loaded`
  - `radar_overlay_point_count=66`
  - `camera_status=source_first_frame_failed`
  - `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `camera_input_signal_check_required=true`
- Live 短 WASD/方向控制复验：
  - forward/back 均 `proxy_status=command_forwarded`、`base_command_mode=ros`、`command_result_ok=true`、`stop_result_ok=true`、`motion_signal_observed=true`。
  - stop 返回 `proxy_status=command_forwarded`、`status=stopped`。
  - 最终 summary `keyboard_continuous_motion_verified=true`、`keyboard_stop_after_release=true`、`keyboard_command_raw_lr_nonzero=true`、`keyboard_wheel_lr_nonzero=false`。

## 剩余风险

- 实时地图、路线、雷达点、小车位置和目标点已经有 live 读回；本轮修正的是 summary 状态合成，地图渲染本身未重写。
- 实时图传仍未完成：当前 DV20 UVC 设备已枚举在 480M USB、无独占，但 V4L2/ffmpeg/共享 MJPEG 都没有真实帧。剩余动作是检查摄像头输入信号、视频线/接口/供电，或换 known-good UVC 后复测。
- WASD/低速手控仍以 PC manual/stop 回包和运动信号证明链路可达；WAVE ROVER `T=1001` wheel raw L/R 非零仍未证明，不能把 IMU/命令到达证据升级为 wheel raw 闭环。
