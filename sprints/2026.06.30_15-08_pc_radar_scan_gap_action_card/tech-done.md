# PC Radar Scan Gap Action Card Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 为 `RobotControlActionStatusCard.evidence` 增加雷达扫描观测缺口字段：`latest_scan_proof_fresh`、`radar_scan_observation_status`、`radar_scan_observation_missing_reasons`、`map_radar_readiness_status`、`map_radar_next_action_plain`、`map_radar_blocked_reason_labels`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 在 `radar_map_points` 动作卡里输出雷达 lifecycle running 但 scan proof 不 fresh、缺少观测或地图雷达层 blocked 时的结构化原因。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏动作卡 DOM 暴露 `data-latest-scan-proof-fresh`、`data-radar-scan-observation-status`、`data-radar-scan-observation-missing-reasons`、`data-map-radar-readiness-status`、`data-map-radar-next-action-plain`、`data-map-radar-blocked-reason-labels`。
  - 当 summary 里只有字符串形式的缺口列表时，前端按逗号拆成数组，避免页面把 `scan_once,scan_hz,raw_packet_once` 当成一个不可读字段。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 增加 summary/action-card 和普通首屏 DOM 断言，锁定地图当前雷达点为 0 时的扫描缺口证据。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步 PC 工作站合同：旧雷达来源点只作诊断，不冒充当前地图贴图；scan proof 不 fresh 或缺观测时地图继续显示 0 个当前雷达点。

## 验证结果

- `curl http://127.0.0.1:7001/`：页面引用 `assets/index-DtJY0Tgm.js` 与 `assets/index-DCA8Xtd4.css`。
- live bundle 检查：`data-latest-scan-proof-fresh`、`data-radar-scan-observation-status`、`data-radar-scan-observation-missing-reasons`、`data-map-radar-readiness-status`、`data-map-radar-next-action-plain`、`data-map-radar-blocked-reason-labels` 均在当前 JS bundle 中命中。
- live summary 检查：`robot_control_executed=false`；雷达 `lifecycle_running=true`、`lifecycle_state=running`、`latest_scan_proof_fresh=false`、`radar_scan_observation_status=missing_required_observations`、缺口为 `scan_once,scan_hz,raw_packet_once`；`radar_map_points.evidence.current_point_count=0`、`source_point_count=81`、`runtime_scan_status=stale`、`map_radar_readiness_status=blocked_missing_scan_observations`。
- live map preview 检查：`robot_control_executed=false`；`radar_overlay_status=not_current`、`radar_overlay_point_count=0`、`radar_overlay_source_point_count=81`、`hard_dangerous_true_fields=[]`。
- sensor-only 雷达 lifecycle 尝试：`POST /api/robot-control/radar/start` 返回 `fetch_timeout_5000ms`，`sensor_lifecycle_only=true`、`robot_control_executed=false`；随后 `POST /api/robot-control/radar/scan-proof/refresh` 返回 `refresh_forwarded`，读回雷达 lifecycle running，但 scan proof 仍 incomplete / not fresh。
- `npm test -- --run`：通过，2 个测试文件、397 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-DtJY0Tgm.js` 与 `dist/assets/index-DCA8Xtd4.css`。
- `git diff --check`：通过。

## 剩余风险

- 本轮没有发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`；没有做真实运动 HIL。
- 上车雷达 lifecycle 已读到 running，但 scan proof 仍缺 `scan_once`、`scan_hz`、`raw_packet_once`，所以 PC 地图当前雷达点仍为 0。
- 旧 `source_point_count=81` 只保留为诊断材料，不能作为当前地图雷达贴图验收。
- 摄像头首帧、Nav2 wheel raw L/R 非零闭环和 delivery 真实闭环仍需后续在安全确认后继续验证。
