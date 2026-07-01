# Radar Overlay Single Endpoint Aliases

## sprint_type

micro

## 实际改动

- 在 `RobotControlSummaryResponse`、`buildRobotControlSummary` 和普通首屏 `plain-live-closure-summary` DOM 中补齐雷达贴图恢复单值 alias：
  - `radar_overlay_readback_endpoint=/api/robot-control/radar/scan-proof/refresh`
  - `radar_overlay_refresh_endpoint=/api/robot-control/radar/scan-proof/refresh`
  - `radar_overlay_status_endpoint=/api/robot-control/radar/status`
  - `radar_overlay_preview_endpoint=/api/robot-control/map/preview`
  - `radar_overlay_summary_endpoint=/api/robot-control/summary`
- 同步 `App.test.ts` 与 `robotControlSummary.test.ts`，保证 summary 和 DOM 都能直接读到这些 endpoint。
- 同步 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，说明这些 alias 只读，不启动雷达 lifecycle、建图 runtime、Nav2/manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

## 验证结果

- `git diff --check`：通过。
- `npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件、427 个用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仅提示现有大 chunk warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `56945`。
- 真实 summary smoke：
  - `status=needs_wheel_rerun`
  - 新增雷达贴图 endpoint alias 全部非空，并与固定恢复序列一致。
  - `map_display_primary_url=/map`
  - `map_display_default_zoom_percent=1600%`
  - `map_display_max_zoom_percent=4800%`
  - `map_display_ros2_companion_answer_plain=ROS2 配套：本地工程调试用 RViz2；远程浏览器观察用 Foxglove bridge + Foxglove Web；普通用户仍默认使用 PC 大地图。`
- 按 summary 暴露的 no-motion 恢复链路执行 `POST /api/robot-control/radar/scan-proof/refresh` 后，回包确认：
  - `readback_only=true`
  - `no_motion_refresh=true`
  - `sends_motion_when_clicked=false`
  - `starts_radar_lifecycle=false`
  - `starts_nav2=false`
  - `starts_manual=false`
  - `starts_keyboard=false`
  - `starts_free_roam=false`
  - `starts_map_runtime=false`
  - `submits_delivery=false`
  - `stops_motion=false`
  - `robot_control_executed=false`
- 刷新后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=148`。
- 刷新后 `GET /api/robot-control/summary` 返回：
  - `live_wysiwyg_missing_surface_ids=["camera"]`
  - `radar_overlay_wysiwyg_complete=true`
  - `radar_overlay_needs_refresh=false`
  - `radar_map_points_visible=true`
  - `mapping_start_missing_reasons=["camera_first_frame"]`

## 剩余风险

- 本轮没有安全确认，未执行任何 motion/control POST，因此没有补 Nav2 wheel raw L/R 非零、delivery success、PC 键盘连续手控或自由移动真实运动验收。
- 当前 WYSIWYG 和建图仍剩相机首帧缺口；现场仍需要处理 USB 12M full-speed / 供电 / 线缆 / known-good UVC 后复测。
- PC 地图合同已是 `/map` 大屏、默认 `1600%`、最高 `4800%`；如果现场仍觉得太小，下一轮应做实际浏览器截图/布局像素验收，而不是引入 RViz2 替代普通用户界面。
