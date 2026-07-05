# PC camera self-hold health refresh

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 修正 `POST /api/robot-control/camera/first-frame/probe`：当远端 probe 返回非 200、无首帧或 `source_busy` 时，PC 代理会在 probe 后再读取一次上车 `/api/camera/health`。
  - 这样相机服务自己持有 `/dev/video1` 的正常共享预览状态，不会被普通 PC 页误报成页面独占或只提示“复测首帧”；如果 health 已经确认 `source_first_frame_failed`，顶层响应会直接显示 `uvc_no_frame_not_exclusive` 和“检查摄像头输入/供电后复测”。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加回归测试，覆盖“第一次 health 只看到 camera service self-hold，远端 probe 返回 source_busy，probe 后 health 才给出无首帧诊断”的现场形态。
  - 同步旧状态缓存测试的 health 请求计数，明确普通 probe 失败后会额外复读 health。
- 文档同步更新：
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
  - `docs/product/pc_tools_workstation.md`
  - `docs/product/pc_free_roam_mapping_design.md`
  - `pc-tools/README.md`

## 验证结果

- `npm test -- test/catalog.test.ts --run -t "workstation camera first-frame probe refreshes health when service self hold masks no-frame diagnosis"`：通过，1 passed。
- `npm run lint`：通过。
- `npm test -- test/App.test.ts test/robotControlSummary.test.ts test/catalog.test.ts --run`：通过，3 files / 453 tests passed。
- `npm run build`：通过，Vite 仅提示大 chunk warning。
- `git diff --check`：通过。
- 真实上位机复验：
  - SSH `root@192.168.1.11 -p 7878` 可连。
  - `trashbot-upper-robot-api`、`trashbot-local-webrtc-camera`、`trashbot-esp32-bridge`、`trashbot-lidar-lifecycle` 均 active。
  - 本机 Node 已重启到 `0.0.0.0:7001`，PID `98160`。
  - PC first-frame probe 返回 `proxy_status=probe_failed`、`status=probe_total_timeout`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_hardware_action_label=检查摄像头输入/供电后复测`、`camera_blocks_free_move=false`。
  - PC `/api/robot-control/live-summary` 返回 `status=ready_for_motion`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`camera_current_visible=false`、`camera_source_diagnosis_status=uvc_no_frame_not_exclusive`、`map_display_default_zoom_percent=1600%`。
  - PC `/api/robot-control/map/preview` 返回地图 PNG、18 个路线点、目标点可见、155 个当前雷达点、`robot_pose_status=map_pose_observed`。
  - PC manual forward/backward 固定代理均返回 `proxy_status=command_forwarded`、`command_raw_lr_nonzero_proven=true`、`stop_result_ok=true`；backward 窗口读到 `motion_signal_observed=true`。
  - PC stop 固定代理返回 `proxy_status=command_forwarded`、`status=stopped`；随后 live-summary 返回 `keyboard_motion_verified=true`、`keyboard_command_raw_lr_nonzero_proven=true`、`keyboard_stop_settled_after_pulse=true`。

## 剩余风险

- 实时图传仍未恢复：DV20/UVC 当前是 `480M`、CMA 正常、共享预览不是页面独占，但没有视频帧。剩余动作仍是检查摄像头输入、视频线、USB 线/接口/供电、采集卡/摄像头本体，或换 known-good UVC 复测。
- WAVE ROVER vendor `T=1001 L/R` 反馈仍为 `0/0`，因此本轮不能宣称 wheel raw L/R 非零或完整自动驾驶/delivery success 闭环完成。硬件口径采用 `docs/vendor/VENDOR_INDEX.md` 中 WAVE ROVER JSON 指令与反馈字段说明。
- ROS2 配套口径保持分层：普通用户优先 PC 首页大地图和 `/map`；本地工程观察用 RViz2/Nav2 RViz 配置，远程浏览器观察用 Foxglove Bridge + Foxglove Web。这些工具不替代 PC 简易控制台，也不发送底盘运动命令。
