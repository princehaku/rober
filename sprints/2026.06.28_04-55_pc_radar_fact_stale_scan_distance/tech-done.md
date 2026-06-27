# 2026.06.28 04:55 PC Radar Fact Stale Scan Distance

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `当前事实` 的雷达行在默认状态下也显示旧 `/scan` 距离过期说明。
- live 若是 `雷达未运行`、runtime scan stale 且还有旧距离/旧雷达点，雷达行会显示“雷达未运行，旧 /scan 距离 ...；旧雷达点 N 个已判定为不当前，未贴到地图”。
- `pc-tools/workstation/test/App.test.ts`：扩展 stopped/stale 雷达 overlay 场景，验证雷达行同时暴露旧距离和旧点未贴图。

## 验证结果

- `npm test -- --run test/App.test.ts -t "not-current map radar overlay summary|stale stopped lidar as not-current|stale runtime scan distance"` 通过，3 passed / 189 skipped。
- `npm test` 通过，2 个 test file / 339 个测试通过。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍有既有 chunk size warning，未影响构建产物。
- `git diff --check` 通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `96302`。
- live 只读 summary（未发任何 POST）确认：lidar lifecycle `stopped/running=false`、fresh `false`、
  continuous `latest_proof_present_but_lifecycle_not_running`、scan points `65/80`，runtime scan
  `stale` 且旧距离 `0.04m`、age `29677.64s`；map `radar_overlay_status=not_current`、overlay points `0`、
  source points `80`；相机仍为 `source_first_frame_failed/uvc_no_frame_not_exclusive`；Nav2 仍为
  `stack=false/lifecycle=stopped`；`robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC 当前事实雷达行；真实雷达仍需现场启动/刷新后才能把新点贴到地图。
