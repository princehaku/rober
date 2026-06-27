# 2026.06.28 04:49 PC Mapping Gap Old Radar Points

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：建图 readiness 的“雷达未刷新”缺口复用 not-current 雷达 overlay 事实。
- 当 summary 已判定旧雷达点不当前且未贴图时，建图缺口显示为“雷达未刷新（旧雷达点 N 个已判定为不当前，未贴到地图）”。
- 旧 `/scan` 距离过期说明仍优先显示；没有距离说明时才使用旧点未贴图说明。
- `pc-tools/workstation/test/App.test.ts`：扩展 stopped/stale 雷达 overlay 场景，验证建图缺口、雷达行、地图行和地图 marker 同步说明旧点未贴图。

## 验证结果

- `npm test -- --run test/App.test.ts -t "not-current map radar overlay summary|stale stopped lidar as not-current|stale runtime scan distance"` 通过，3 passed / 189 skipped。
- `npm test` 通过，2 个 test file / 339 个测试通过。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍有既有 chunk size warning，未影响构建产物。
- `git diff --check` 通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `87010`。
- live 只读 summary（未发任何 POST）确认：lidar lifecycle `stopped/running=false`、fresh `false`、
  continuous `latest_proof_present_but_lifecycle_not_running`、scan points `65/80`，runtime scan
  `stale` 且旧距离 `0.04m`；map `radar_overlay_status=not_current`、overlay points `0`、source points
  `80`；free-roam 建图缺口仍包含 `camera_first_frame/lidar_fresh/mapping_active/fresh_map_preview`；
  相机仍为 `source_first_frame_failed/uvc_no_frame_not_exclusive`；Nav2 仍为 `stack=false/lifecycle=stopped`；
  `robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC 建图缺口文案；真实建图验收仍需要 camera first frame、fresh radar、mapping active 和 fresh map preview 同时满足。
