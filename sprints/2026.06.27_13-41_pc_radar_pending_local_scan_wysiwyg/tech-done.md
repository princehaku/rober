# PC radar pending local scan WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当雷达 lifecycle 在运行但 proof stale，且没有 map-frame 机器人位姿时，不再把已有 `scan_preview_points` 隐藏成“仅点数”。
  - 地图右上角局部点云会显示为 `待刷新局部点`，caption 写明“正在确认实时性，当前先显示局部轮廓”。
  - 保持保护：如果已经有 map 位姿但 proof stale，旧点数组仍不贴到地图坐标。
- `pc-tools/workstation/src/styles.css`
  - 新增 `待刷新局部点` 的琥珀色虚线视觉态，区别于绿色实时点和最近记录点。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 live 形态合同测试：running + stale + no pose + scan points 时显示 pending local dots。
  - 继续验证 stale mapped radar points 不会贴到地图。
- `docs/product/pc_tools_workstation.md`
  - 同步记录待刷新局部点口径。

## 验证结果

- `npm test -- --run App.test.ts -t "draws stale running radar scan points as pending local dots"`
  - 结果：通过，`1 passed | 164 skipped`。
- `npm test -- --run App.test.ts -t "keeps stale mapped radar point arrays off the map"`
  - 结果：通过，`1 passed | 164 skipped`。
- `npm test`
  - 结果：通过，`2 passed`，`289 passed`。
- `npm run build`
  - 结果：通过，生成 `dist/`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮地图雷达 overlay。
- `curl -sS 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' | jq '{pose: .o3_proof_summary.robot_pose, scan_points: (.o3_proof_summary.scan_preview_points | length), scan_count:.o3_proof_summary.scan_preview_point_count, lidar:{continuous_scan_status:.readback_summary.lidar.continuous_scan_status,lifecycle_running:.readback_summary.lidar.lifecycle_running,continuous_window_observed:.readback_summary.lidar.continuous_window_observed,latest_scan_proof_fresh:.readback_summary.lidar.latest_scan_proof_fresh,scan_preview_point_count:.readback_summary.lidar.scan_preview_point_count,scan_preview_frame_id:.readback_summary.lidar.scan_preview_frame_id}}'`
  - 结果：通过；live 当前已恢复为 `robot_pose.frame_id=map`、`scan_points=65`、`continuous_scan_status=latest_proof_fresh_while_lifecycle_running`、`latest_scan_proof_fresh=true`。因此现场当前会走实时贴图路径；本轮新增的 stale/no-pose 待刷新局部点路径由上方合同测试覆盖。

## 剩余风险

- 本轮只修正 PC 地图展示口径，不刷新雷达、不修复上车端 `latest_scan_proof_stale` 根因。
- 当前 live 雷达仍需现场刷新/排查连续扫描 freshness；摄像头仍是 UVC 无首帧。
- 本轮不启动 free-roam、不执行 Nav2、不发送 manual/keyboard/delivery/stop 或 `/cmd_vel`。
