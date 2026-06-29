# PC 建图解锁包

sprint_type: micro

## 实际改动

- 普通首屏“自由移动准备”新增“建图解锁包”，固定显示先自由移动、画面首帧、雷达新鲜、建图启动四行。
- 解锁包直接消费 Robot Control summary 的 camera/radar/free_roam readiness：自由移动只看安全确认和停止兜底；画面首帧、雷达新鲜只影响建图启动和验收。
- 每行“去处理”只聚焦到已有控件，不自动勾选、不启动雷达、不启动自由移动、不启动建图、不发送任何运动指令。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`，1 passed。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "shows shared preview auto-join when camera readback is online"`，1 passed。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "keeps camera preview in waiting state until the browser draws a video frame"`，1 passed。
- 通过：`npm --prefix pc-tools/workstation test`，2 files / 376 tests passed。
- 通过：`npm --prefix pc-tools/workstation run build`。
- 通过：PC API 已重启到 `0.0.0.0:7001`，PID `91578`。
- 通过：只读 `GET /api/robot-control/summary` 返回 `free_roam_motion_start_ready=true`、`free_roam_mapping_start_ready=false`、
  `free_roam_mapping_start_missing_reasons=["camera_first_frame","lidar_fresh"]`。

## 剩余风险

- 本轮只增强 PC 端解锁视图，不触发真实传感器启动或建图启动；live 建图仍需要真实画面首帧和新鲜雷达扫描。
- live 摄像头当前仍是 `source_first_frame_failed / uvc_no_frame_not_exclusive / has_recent_frame=false`，即不是页面独占但 UVC 无首帧。
- live 雷达当前仍是 `radar_stopped / lifecycle_running=false / latest_scan_proof_fresh=false / map_marker_point_count=0`。
