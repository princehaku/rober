# PC 读取最近 Nav2 结果后同步刷新地图画面

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `loadNavGoalExecutionLatestAndRefreshMap()`。
  - 普通首屏“重新读取行程（只读）”和高级“读取最近 Nav2 结果（高级）”现在先读最近 Nav2 结果，再只读刷新地图预览。
  - 页面初始预载仍只读 latest，不额外触发地图刷新，避免加载阶段重复抢占地图刷新状态。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展最近行程 pending 回归测试：点击读取行程时仍不执行 Nav2、不发 manual、不确认 delivery、不触碰 `/cmd_vel`；latest 返回后必须额外读取一次 `/api/robot-control/map/preview`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录“读取最近 Nav2 结果后同步刷新地图画面”的 PC 所见即所得行为。

## 验证结果

- `npm run build`：通过。
- `npm test -- App.test.ts --testNamePattern "trip latest|最近行程|map-level pending"`：通过，`2 passed / 216 skipped`。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID 为 `6702`。
- live `GET http://127.0.0.1:7001/api/robot-control/nav2/goal/execution/latest`：
  - `proxy_status=latest_loaded`
  - `status=loaded_fail_closed_summary`
  - `remote_endpoint=/api/nav2/goal/execution/latest`
  - `robot_control_executed=false`
  - `goal_execution_status=goal_succeeded`
  - `result_status=succeeded`
  - `feedback_sample_count=8`
  - `evidence_ref=o11-nav2-goal-execution-1782500121051`
- live `GET http://127.0.0.1:7001/api/robot-control/map/preview`：
  - `proxy_status=preview_forwarded`
  - `robot_control_executed=false`
  - `robot_pose_status=map_pose_observed`
  - `path_preview_status=path_preview_observed`
  - `path_preview_point_count=18`
  - `radar_overlay_status=not_loaded`
  - `radar_overlay_count=0`
- live `GET http://127.0.0.1:7001/api/robot-control/summary`：
  - `robot_api_connection.status=readable`
  - `readback_summary.nav2.status=goal_succeeded_wheel_feedback_not_proven`
  - `safe_command_boundary.nav2_goal_ready=true`
  - `readback_summary.free_roam.motion_start_ready=true`
  - `readback_summary.map.path_preview_status=path_preview_observed`
  - `readback_summary.map.radar_overlay_status=not_loaded`

## 剩余风险

- 本轮只改 PC 端只读刷新串联，不执行真实 Nav2 路线、不证明 wheel raw L/R 非零、不确认 delivery success。
- live 仍显示最近 Nav2 为 `goal_succeeded_wheel_feedback_not_proven`，说明路线成功但 wheel raw L/R 非零未证明。
- live 地图路线和小车位置可见，但雷达 overlay 仍为 `not_loaded/0`；需要启动雷达并等新扫描后刷新地图画面。
- 摄像头首帧、雷达新鲜点、真实自动驾驶移动仍依赖现场上车端状态和安全确认后的实车验证。
