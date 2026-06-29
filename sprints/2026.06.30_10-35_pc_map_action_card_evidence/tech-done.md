# 2026.06.30 10:35 PC 地图动作卡证据

sprint_type: micro

## 设计先行

本轮补 PC 首屏“地图”动作卡的结构化只读证据，并把普通用户地图默认放大，不刷新地图、不启动雷达、不执行 Nav2 或任何运动命令。目标是让人眼和脚本都能确认：地图画面是不是当前可见、图上路线是否画出、小车位置是否可见、雷达点是否贴到当前地图，以及地图可通行格数量。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `map_preview.evidence`，增加地图画面、路线、小车位置、雷达点和 free cell 证据字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `map_preview` 动作卡输出 `map_current_visible`、`path_visible_on_map`、`robot_pose_visible`、`radar_points_visible_on_map` 等只读证据。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏兼容旧 summary，从 `readback_summary.map/localization/radar` 补地图证据，并暴露 DOM `data-*` 属性。
  - 增加地图“大图模式”前端状态，默认大图，可用“收起地图/放大地图”切换。
- `pc-tools/workstation/src/styles.css`
  - 地图面板横跨整行，默认使用响应式大地图高度；移动端使用较小高度兜底。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 summary 中 `map_preview.evidence` 的地图/路线/小车位置/雷达点字段。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通首屏 DOM 上能读到地图 WYSIWYG 证据、大图默认状态、切换按钮和 CSS 尺寸规则。
- `pc-tools/README.md`
  - 同步记录地图动作卡证据合同、大图模式、RViz2 工程调试建议和不触发动作边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 167 skipped (168)`。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 217 skipped (218)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过；仅保留 Vite chunk size 提示。
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`，`Tests 386 passed (386)`。
- 通过：`git diff --check`。
- 通过：重启本机 PC Node 到 `0.0.0.0:7001`。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`。
  - `/tmp/rober_pc_workstation_7001.log` 显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读请求 `http://127.0.0.1:7001/api/robot-control/summary`。
  - `map_preview.status=visible`。
  - `map_current_visible=true`、`map_free_cell_count=425`。
  - `path_visible_on_map=true`、`path_point_count=18`、`path_frame_id=map`。
  - `robot_pose_visible=true`。
  - `radar_points_visible_on_map=false`、`radar_point_count_on_map=0`。
  - `radar_map_points.status=not_current`，`source_point_count=81`，`blocked_reasons=radar_lifecycle_not_running_for_map_radar_points`。
  - live 结论：地图画面、图上路线和小车位置当前已可见；雷达来源点存在但雷达未运行，所以当前不贴图，脚本可直接读出雷达点不是当前地图所见。

## 剩余风险

- 本轮只补只读合同、DOM 验证和 PC 端显示尺寸，不刷新地图、不启动雷达、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实建图闭环仍依赖相机首帧、地图记录和地图画面刷新；当前 live 主要缺口仍是 UVC 摄像头无首帧。
