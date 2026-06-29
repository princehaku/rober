# PC summary radar missing observations

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：PC summary 从上车
  `/api/radar/status.blocked_reasons` 和 scan-proof latest 中提取雷达扫描观测缺口。
  当缺 `scan_once/scan_hz/raw_packet_once` 时，`readback_summary.lidar/radar` 会暴露
  `radar_scan_observation_status`、`radar_scan_observation_missing_reasons`、
  `radar_map_overlay_readiness_status` 和 `radar_map_overlay_next_action_plain`。
- `pc-tools/workstation/src/shared/contracts.ts`：为 summary 的 `lidar` 和 `radar` readback
  补充可选缺口字段，保持旧 fixture 兼容。
- `pc-tools/workstation/test/catalog.test.ts`：扩展 running/incomplete 雷达回归，确认普通
  action card 和 goal summary 会直接显示缺 `scan_once,scan_hz,raw_packet_once`，而不是泛泛提示刷新雷达状态。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录 summary 首屏的只读雷达缺口口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "preserves radar raw-packet parsed status"`，
  结果 `1 passed | 167 skipped`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `77174`。
- 通过：只读 live `GET http://127.0.0.1:7001/api/robot-control/summary` 返回
  `readback_summary.lidar.radar_scan_observation_status=missing_required_observations`、
  `readback_summary.lidar.radar_scan_observation_missing_reasons=scan_once,scan_hz,raw_packet_once`、
  `readback_summary.radar.radar_status_plain=雷达已运行但扫描 proof 缺 scan_once、scan_hz、raw_packet_once；地图雷达点当前显示 0 个。`、
  `action_status_cards[radar_map_points].next_action_plain=先修复雷达扫描观测：scan_once、scan_hz、raw_packet_once；有新扫描后再刷新地图画面`、
  `goal_checklist_summary.radar_next_action_plain=先修复雷达扫描观测：scan_once、scan_hz、raw_packet_once；有新扫描后再刷新地图画面`。

## 剩余风险

- 本轮只把雷达缺口推进到 PC summary 首屏，不修复上车 LiDAR proof 采样本身。
- 当前真实车仍可能保持雷达 lifecycle running 但 scan proof 不 fresh；地图会继续不贴雷达点。
- 本轮不执行 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`，不提供真实运动完成证明。
