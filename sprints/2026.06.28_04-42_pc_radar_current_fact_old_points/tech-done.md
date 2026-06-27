# 2026.06.28 04:42 PC Radar Current Fact Old Points

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `当前事实` 的雷达行新增 not-current 旧点说明。
- 当 summary 明确旧雷达点不能作为当前 overlay 时，雷达行会显示“雷达未运行；旧雷达点 N 个已判定为不当前，未贴到地图”，和地图行、地图 marker、雷达点口径保持一致。
- `pc-tools/workstation/test/App.test.ts`：扩展 stopped/stale 雷达 overlay 场景，验证雷达行与地图行都显示旧点未贴图，并且不回画旧点。

## 验证结果

- `npm test -- --run test/App.test.ts -t "not-current map radar overlay summary|stale stopped lidar as not-current"` 通过，2 passed / 190 skipped。
- `npm test` 通过，2 个 test file / 339 个测试通过。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍有既有 chunk size warning，未影响构建产物。
- `git diff --check` 通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `74875`。
- live 只读 summary（未发任何 POST）确认：lidar lifecycle `stopped/running=false`、fresh `false`、
  continuous `latest_proof_present_but_lifecycle_not_running`、scan points `65/80`；map
  `radar_overlay_status=not_current`、overlay points `0`、source points `80`，blocked reasons 包含
  runtime scan stale、radar lifecycle not running 和 robot pose missing；相机仍为
  `source_first_frame_failed/uvc_no_frame_not_exclusive`；Nav2 仍为 `stack=false/lifecycle=stopped`；
  `robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC 首屏雷达事实文案；真实雷达仍需现场启动/刷新，地图 overlay 仍依赖 fresh 雷达、robot pose 和地图预览。
