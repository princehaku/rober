# PC Stale Radar Points Not Mapped

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - pending 雷达状态（启动中、待刷新、无新点、刷新中）下，即使 summary 带旧 `scan_preview_points` 数组，也不再绘制地图点或局部点。
  - 地图 marker/caption 保留点数材料，显示为 `待刷新雷达点 N 个（旧点数组，未贴到地图）`，并继续显示最近障碍距离。
  - fresh 状态仍允许真实点数组按 map pose/外参贴图；无 pose 时仍只显示实时局部轮廓。
- `pc-tools/workstation/test/App.test.ts`
  - 将 stale proof + map pose + scan point array 的回归改为反向断言：不渲染 `plain-map-radar-scan-points` / `plain-map-radar-local-scan`。
- `docs/product/pc_tools_workstation.md`
  - 记录 stale radar proof 的地图 WYSIWYG 口径：旧点数组只能作为待刷新材料，不能画成地图实时点。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "stale mapped radar point arrays|radar point|running lidar|radar marker"`，8 passed / 279 skipped。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`；仅有既有 Vite chunk size warning。
- 已通过：`cd pc-tools/workstation && npm test`，2 files / 287 tests passed。
- 已通过：`git diff --check`。
- 已通过：`launchctl kickstart -k gui/$(id -u)/com.rober.pc.api.7001 && sleep 5 && lsof -nP -iTCP:7001 -sTCP:LISTEN`；`node` 监听 `TCP *:7001 (LISTEN)`。
- live 只读 summary 检查：当前真实形态为 `latest_scan_proof_fresh=false`、`continuous_scan_status=latest_proof_stale_while_lifecycle_running`，但 summary 仍带旧 `scan_preview_points_len=72`、`scan_preview_point_count=72`、`scan_preview_frame_id=laser_frame`；本轮 UI 回归覆盖该形态并确认旧点数组不再绘制成地图点。

## 剩余风险

- 本轮只修 PC 地图显示，不启动雷达、不刷新 proof、不发 manual/free-roam/Nav2/stop 或 `/cmd_vel`。
- live 当前雷达 runtime `/scan` 是新鲜的，但 `/api/radar/status` proof 仍 stale；本轮确保旧点不被画成实时地图点，未修 proof collector 本身。
- 摄像头真实首帧和 Nav2 同窗口 wheel raw L/R 非零仍未完成。
