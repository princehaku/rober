# PC 相机代理超时缓存与运行态复验 micro sprint

sprint_type: micro

## 实际改动

- 修正 PC Node 相机首帧探针缓存：`probe_failed` 不再自动等同“相机源头无帧”；只有上车 probe/fallback 明确返回首帧/读帧失败时，才写入 `cameraFirstFrameProbeLastFailures`。
- 补充回归测试：先缓存 `probe_total_timeout / uvc_no_frame_not_exclusive`，再模拟 `backendSmoke` 代理层 `fetch_timeout_45000ms`，确认 `/api/robot-control/camera/mjpeg/status` 仍保持 `source_first_frame_failed`，不会降级回 `source_selected_not_probed`。
- 同步 `OKR.md`、`pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md` 和 `docs/process/okr_progress_log.md`，写明当前有效事实：地图默认 `1600%`、ROS2 配套为 RViz2/Foxglove 工程观察，实时图传仍未恢复。

## 验证结果

- 通过：`npm test -- test/catalog.test.ts --run -t "workstation camera MJPEG status keeps recent first-frame probe failure after camera service restart"`。
- 通过：`npm run lint`。
- 通过：`npm test -- test/App.test.ts test/robotControlSummary.test.ts test/catalog.test.ts --run`，结果 `Test Files 3 passed`、`Tests 452 passed`。
- 通过：`npm run build`，TypeScript/Vite 构建完成；保留既有 Vite chunk size warning。
- 通过：`git diff --check`。
- 运行态已复验：PC 7001 监听 `0.0.0.0:7001`；map preview 显示地图、18 点 Nav2 路线、目标点、小车位置和 152 个当前雷达点；live-summary 显示 `map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`；WASD 前进/后退/stop 返回 `command_forwarded`、命令 raw L/R 非零、stop OK 与 IMU 动作信号。
- 相机硬件证据：DV20 `/dev/video1` 为 USB `480M`，无外部 owner，CMA 正常；OpenCV/v4l2-ctl/ffmpeg 以及 `uvcvideo quirks/nodrop/timeout` 参数矩阵均未读到任何帧，直接 probe 返回 `capture_read_call_timeout` / `backend_no_frame_observed`。

## 剩余风险

- 实时图传仍未完成，不能宣称真实 RTC/视频已恢复；剩余指向 DV20 上游输入、视频线、接口、供电、采集卡/摄像头本体或换 known-good UVC 复测。
- WAVE ROVER vendor `T=1001 L/R` 仍为 `0/0`，不能宣称 wheel raw 非零；当前只能证明命令 raw 非零、HTTP/PWM/ROS 手控链路和 IMU 动作信号。
- 本轮没有启动 RViz2/Foxglove，也没有改变 ROS2 graph、Nav2 行为、底盘参数或相机硬件配置。
