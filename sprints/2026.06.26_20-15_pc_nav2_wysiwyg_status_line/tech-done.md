# PC Nav2 WYSIWYG 状态行 Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通地图 caption 新增 `行程读数`，把 `readback_summary.nav2/localization` 翻成普通用户可理解的状态。
- `pc-tools/workstation/test/App.test.ts`：补默认阻塞场景和“路径已生成但 map 坐标缺失”场景，锁定首屏可见文案。
- `docs/product/pc_tools_workstation.md`：同步说明普通首屏现在会直接暴露路径、定位和行程服务读数。

## 验证结果

- `npm test -- App.test.ts`：通过，136 tests passed。
- `npm test`：通过，2 files / 239 tests passed。
- `npm run build`：通过；Vite 保留既有大 chunk warning。
- PC Node 已重启到 `0.0.0.0:7001`，`/api/health` 正常，监听进程为 `node` PID `92561`。
- live summary 默认地址命中 `http://192.168.1.11:8787`：`map.map_once_observed=true`，`nav2.path_generated=true`，`nav2.path_preview_point_count=36`，`nav2.path_preview_frame_id=map`，`localization.robot_pose_status=pose_signal_observed_without_map_coordinates`。

## 剩余风险

- 本轮只改 PC 首屏解释和测试，不修复上车端定位坐标缺失。
- live camera 当前是 `status=ready` 但 `source_readiness=source_selected_not_probed`，不等于已经看到首帧。
- live base 当前 `wheel_feedback_latest_left_speed=0`、`wheel_feedback_latest_right_speed=0`，仍未证明本轮非零运动。
- Nav2 已生成 36 点路径，但 `robot_pose_x/y=not_loaded`，所以不能宣称完整自动驾驶执行已修好。
