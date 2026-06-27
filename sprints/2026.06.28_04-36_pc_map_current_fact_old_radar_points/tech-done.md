# 2026.06.28 04:36 PC Map Current Fact Old Radar Points

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `当前事实` 的地图行新增 not-current radar overlay 短说明。
- 当 summary 明确 `radar_overlay_status=not_current` 且仍有旧 source 点数时，地图事实行会显示“旧雷达点 N 个已判定为不当前，未贴到地图”，和地图 marker / 雷达点口径保持一致。
- `pc-tools/workstation/test/App.test.ts`：扩展 stopped/stale 雷达 overlay 场景，验证当前事实、地图 marker 和雷达点口径三处一致，且不回画旧雷达点。

## 验证结果

- `npm test -- --run test/App.test.ts -t "not-current map radar overlay summary|stale stopped lidar as not-current"` 通过，2 passed / 190 skipped。
- `npm test` 通过，2 个 test file / 339 个测试通过。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍有既有 chunk size warning，未影响构建产物。
- `git diff --check` 通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `64384`。
- live 只读 summary（未发任何 POST）确认：`radar_overlay_status=not_current`、overlay point count `0`、
  source points `80`，blocked reasons 为 `runtime_scan_stale_for_map_radar_overlay`、
  `radar_lifecycle_not_running_for_map_radar_overlay`、`robot_pose_missing_for_map_radar_overlay`；
  lidar lifecycle `stopped`、fresh `false`、scan points `65/80`；相机仍为
  `source_first_frame_failed/uvc_no_frame_not_exclusive`；Nav2 仍为 `stack=false/lifecycle=stopped`；
  `robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC 首屏地图事实文案；真实雷达 lifecycle stopped、runtime scan stale 和 robot pose missing 仍需现场启动/刷新雷达、恢复定位后验证。
