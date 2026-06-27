# PC Node 7001 热更新雷达 Overlay 口径

## sprint_type

micro

## 实际改动

- 重启本机 PC workstation API：
  - 停止旧 `tsx src/server/index.ts` 进程。
  - 使用 `HOST=0.0.0.0 PORT=7001 npm run api:public` 重新启动。
- 未修改产品代码；本轮只让已提交代码在 7001 运行进程生效。
- 旧日志写入 `/tmp/rober-workstation-7001.log`，不改仓库配置。

## 验证结果

- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：
  - 新 `node` 进程监听 `TCP *:7001`。
- 只读复验 `GET http://127.0.0.1:7001/api/robot-control/summary`：
  - `console_status=loaded_fail_closed_summary`
  - `robot_api_connection.status=readable`
  - `readback_summary.map.radar_overlay_status=not_current`
  - `readback_summary.map.radar_overlay_scan_preview_point_count=0`
  - `readback_summary.map.radar_overlay_blocked_reasons=runtime_scan_stale_for_map_radar_overlay,radar_lifecycle_not_running_for_map_radar_overlay,robot_pose_missing_for_map_radar_overlay`
  - `readback_summary.lidar.lifecycle_state=stopped`
  - `readback_summary.lidar.runtime_scan_status=stale`
  - `readback_summary.free_roam.motion_start_ready=true`
  - `readback_summary.free_roam.mapping_ready=false`
  - `readback_summary.nav2.planner_server_active=false`
  - `readback_summary.nav2.controller_server_active=false`

## 剩余风险

- 本轮没有发送任何 free-roam、manual、Nav2、delivery、stop 或 `/cmd_vel` 命令。
- 雷达当前仍是 stopped/stale；地图不再把旧点当当前 overlay，但要显示当前雷达点仍需现场启动/刷新雷达。
- 摄像头仍是 `source_first_frame_failed/first_frame_total_timeout`；建图验收仍缺 camera first frame。
- Nav2 planner/controller 仍未 active；完整路线执行前仍需先恢复自动驾驶服务。
