# ROS2 Companion Plain Alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：给地图/ROS2 配套读回增加 `map_display_ros2_companion_plain` 短 alias，类型与既有 `map_display_ros2_companion_answer_plain` 同源。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 顶层和 `live_closure_summary` 同步返回 `map_display_ros2_companion_plain`，用于现场 `curl | jq` 直接读取 ROS2 配套白话答案。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-live-map-companion-summary` 增加 `data-ros2-companion-plain`，用于 DOM smoke 直接确认 RViz2/Foxglove 只作工程观察。
- 同步更新 `App.test.ts`、`robotControlSummary.test.ts`、`pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；保留既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `85577`。
- 真实 summary 只读 smoke 返回 `map_display_primary_url=/map`、默认缩放 `1600%`、最高 `4800%`、`map_display_ros2_companion_plain=ROS2 配套：本地工程调试用 RViz2；远程浏览器观察用 Foxglove bridge + Foxglove Web；普通用户仍默认使用 PC 大地图。`，并保持 `map_display_starts_ros2=false`、`starts_rviz2=false`、`starts_foxglove=false`、`starts_nav2=false`、`starts_map_runtime=false`。
- 重启后雷达贴图一度 stale，按已声明 no-motion 链路执行 `POST /api/robot-control/radar/scan-proof/refresh -> GET /api/robot-control/radar/status -> GET /api/robot-control/map/preview -> GET /api/robot-control/summary` 后恢复为 `live_wysiwyg_missing_surface_ids=[camera]`、`radar_overlay_wysiwyg_complete=true`、`radar_map_points_visible=true`。refresh 回包证明 `readback_only=true`、`no_motion_refresh=true`、所有 `starts_*`、`submits_delivery`、`stops_motion` 和 `robot_control_executed` 均为 false。

## 剩余风险

- 本轮未发任何运动/control POST，未执行 Nav2、键盘连续手控、自由移动、建图或 delivery complete。
- 真实 motion 目标仍缺安全确认后的完整 Nav2 路线同窗口 wheel raw L/R 非零、delivery success、PC 键盘连续手控和自由移动运行读回。
- 当前 WYSIWYG 和建图启动仍只剩相机首帧硬件缺口。
