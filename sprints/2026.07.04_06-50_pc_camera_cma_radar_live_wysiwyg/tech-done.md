# PC 相机 CMA 诊断与雷达贴图复核

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`：相机 smoke health 增加 CMA 内存诊断，首帧失败且 UVC 非独占、近期 `cma_alloc` 失败时输出 `uvc_cma_alloc_failed_not_exclusive`。
- `onboard/scripts/upper_robot_api.py`：上位机 camera/mjpeg status 扁平透出 `cma_memory_diagnostics_*`、中文下一步和 `释放内存/重启后复测` 硬件动作。
- `pc-tools/workstation/src/server/index.ts`、`robotControlSummary.ts`、`contracts.ts`：PC 直连 status、summary/live-summary 同步识别 CMA 诊断，保持 `camera_blocks_free_move=false`、`camera_blocks_mapping_start=true`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：补 CMA 诊断优先级回归。
- `docs/product/pc_free_roam_mapping_design.md`、`docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`、`OKR.md`：同步 O7 现场证据、接口合同和剩余风险。

## 验证结果

- `npm test -- test/robotControlSummary.test.ts --run`：18 tests passed。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/upper_robot_api.py`：通过。
- `npm run build`：通过，仅保留既有 Vite chunk size warning。
- PC 7001 已重启并监听 `0.0.0.0:7001`；`GET /` 与 `GET /map` 均 HTTP 200。
- 真实上位机 8787/8088 相机状态：`source_diagnosis_status=uvc_cma_alloc_failed_not_exclusive`、`hardware_action_label=释放内存/重启后复测`、`cma_memory_diagnostics_status=cma_alloc_failed_recent`。
- PC 7001 `GET /api/robot-control/camera/mjpeg/status`：返回同源 CMA 诊断、中文 next action、`hardware_action_required=true`、`camera_blocks_free_move=false`、`camera_blocks_mapping_start=true`。
- 雷达复核：启动既有 LiDAR lifecycle 后 `/scan` 有 publisher，`ros2 topic echo --once /scan` 读到 LaserScan；只读刷新后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=117`、`radar_overlay_wysiwyg_complete=true`，live-summary 返回 `radar_map_points_visible=true`。

## 剩余风险

- 相机仍没有真实首帧；下一步必须释放上位机内存或重启后复测，仍无画面再换 known-good UVC。
- LiDAR lifecycle 本轮为恢复现场雷达贴图而启动；脚本边界显示不使用 `/dev/ttyS5`、不发布 `/cmd_vel`，但后续若上位机重启仍需确认雷达 lifecycle 是否自动拉起。
- wheel raw `T=1001 L/R` 仍为 `0/0`，不能把 command raw + IMU 运动信号升级成 wheel feedback 闭环。
- 完整 Nav2 路线 HIL、delivery success、真实 RTC/视频仍未完成。
