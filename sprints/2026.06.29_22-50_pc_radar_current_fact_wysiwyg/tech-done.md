# PC 当前事实雷达贴图 WYSIWYG 口径

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当地图雷达 overlay 已 `loaded/partial` 且实际显示点数大于 0 时，`readback_summary.radar.radar_status_plain`、`radar_next_action_plain` 和 `plain_hint` 优先采用地图 overlay 的 WYSIWYG 事实。
  - `radar_scan_observation_missing_reasons` 等高级诊断字段继续保留 `raw_packet_once` 等缺口，但不再压过普通首屏的地图贴图事实。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补充回归断言：地图 radar overlay 已贴图时，普通 radar summary 和 `current_fact_plain` 不再提示“先修复雷达扫描观测”。
- `docs/product/pc_tools_workstation.md`
  - 记录 current fact 也必须跟随地图 overlay WYSIWYG 的产品口径。
- `docs/process/okr_progress_log.md`
  - 追加本轮 Objective 3 雷达地图 WYSIWYG 进展。

## 验证结果

- `npm test -- catalog.test.ts -t "running radar lifecycle"`：通过，1 test OK。
- `npm test -- --run`：通过，2 个 test files，386 tests OK。
- `npm run build`：通过，`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` OK。
- 重启 PC Node 到 `0.0.0.0:7001` 后只读验证 live summary：
  - `radar_overlay_status=loaded`
  - `radar_overlay_point_count=72`
  - `radar_status_plain=雷达点已贴到当前地图：当前显示 72 个点，frame=laser_frame`
  - `radar_next_action_plain=继续观察地图雷达层`
  - `radar_scan_observation_missing_reasons=raw_packet_once` 仍保留为高级诊断
  - `current_fact_plain` 不再包含“先修复雷达扫描观测”

## 剩余风险

- 本轮不启动雷达、不刷新地图、不发任何运动命令；真实新扫描和 raw packet proof 缺口仍需现场工程验证。
- 当前 live 仍显示摄像头无首帧，因此建图启动还缺“画面首帧”；自由移动不受该缺口阻塞。
