# PC 雷达旧点贴图刷新计划

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当地图雷达 `当前点=0` 且 `来源点>0` 被判定为旧读数抑制时，live WYSIWYG 诊断不再显示含混的“还差=无”。
  - 新增 `live_wysiwyg_radar_map_refresh_next_action_plain`、`live_wysiwyg_radar_map_refresh_sequence`、`live_wysiwyg_radar_map_refresh_sequence_labels`，明确下一步是先刷新雷达扫描读数，再刷新地图画面。
  - 同步把雷达贴图刷新 label 从工程词改成普通用户可读的“刷新雷达扫描读数”。
- `pc-tools/workstation/src/server/index.ts`
  - 对齐 catalog/fixture 侧的雷达贴图 next action 文案，避免 Node catalog 与 summary helper 口径漂移。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当前卡点和 WYSIWYG 诊断 DOM 暴露 `data-radar-map-refresh-*` 字段，并在普通首屏显示旧来源点已抑制和 no-motion 刷新顺序。
  - 当前所见刷新序列 fallback 也改为“雷达扫描读数”，避免普通首屏泄漏内部 proof 术语。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 live closure summary 类型合同。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 覆盖旧雷达来源点被抑制时的诊断文案、结构化刷新序列和 DOM 字段。
- `docs/product/pc_tools_workstation.md`
  - 同步记录雷达 stale 来源点的 WYSIWYG 刷新合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts test/App.test.ts -t "stale radar|same-window wheel|plain-live-closure|radar map"`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test -- --run`，结果 `Test Files 3 passed (3)`、`Tests 413 passed (413)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。
- 通过：重启 `PORT=7001 HOST=0.0.0.0 npm run api` 后只读 `GET http://127.0.0.1:7001/api/robot-control/summary` smoke：
  - `source_base_url=http://192.168.1.11:8787`
  - `status=needs_wheel_rerun`
  - `map_current_visible=true`
  - `radar_map_points_visible=false`
  - `live_wysiwyg_radar_map_stale_source_points_suppressed=true`
  - `live_wysiwyg_radar_map_current_point_count=0`
  - `live_wysiwyg_radar_map_source_point_count=123`
  - `live_wysiwyg_radar_map_refresh_next_action_plain=旧雷达来源点 123 个已抑制；先刷新雷达扫描读数，再刷新地图画面，确认同轮雷达点贴图。`
  - 可见雷达刷新文案未包含 `proof`。

## 剩余风险

- 本轮只改 PC 只读 summary/DOM/文案，不实际刷新雷达 proof 或地图画面。
- 没有触发任何 Nav2、manual、keyboard、free-roam、delivery、stop、建图或 `/cmd_vel` 运动接口。
