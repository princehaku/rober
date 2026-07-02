# 2026-07-02 08:24 CST current wysiwyg action PC UI

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 summary 顶层 `current_wysiwyg_action_*` 短字段，直接表达当前 WYSIWYG 缺口该走哪条只读刷新链。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐 `RobotControlSummaryResponse` 的 `current_wysiwyg_action_*` 类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainCurrentWysiwygActionGauge`，优先消费 summary 顶层短字段。
  - 在现场验收卡顶部新增 `plain-current-wysiwyg-action` 短行，显示当前所见动作、缺口和只读链路。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖 `current_wysiwyg_action_*` 与原 primary no-motion readback 字段同源。
- `pc-tools/workstation/test/App.test.ts`
  - 补 fixture 顶层 `current_wysiwyg_action_*`，并覆盖普通首屏 DOM 短行。
- `docs/product/pc_tools_workstation.md`
  - 同步记录当前所见只读动作的产品边界。

## 验证结果

- `npm test -- --run App.test.ts robotControlSummary.test.ts`
  - 通过：`Test Files 2 passed (2)`，`Tests 247 passed (247)`。
- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`
  - 通过：`Test Files 3 passed (3)`，`Tests 428 passed (428)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`；仅保留 Vite 既有 chunk size warning。
- `git diff --check`
  - 通过，无空白错误。
- 重启 PC Node：
  - 已用 `PORT=7001 HOST=0.0.0.0 ROBOT_CONTROL_DEFAULT_BASE_URL=http://192.168.1.11:8787 npm run api` 重启。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`，PID `50101`。
- 只读 smoke：
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 通过，读到 `current_wysiwyg_action_id=refresh_current_wysiwyg`、`current_wysiwyg_action_label=刷新当前所见`、`current_wysiwyg_action_endpoint=/api/robot-control/radar/scan-proof/refresh`、`current_wysiwyg_action_method=POST`、`current_wysiwyg_action_sequence=[radar scan-proof, radar status, map preview, camera first-frame probe, camera MJPEG status, summary]`、`current_wysiwyg_action_missing_surface_ids=[camera,radar_map_points]`、`current_wysiwyg_action_refresh_mode=all_wysiwyg`。
  - 同一 summary 明确 `current_wysiwyg_action_sends_motion=false`、`current_wysiwyg_action_starts_radar_lifecycle=false`、`current_wysiwyg_action_starts_map_runtime=false`、`current_wysiwyg_action_starts_nav2=false`、`current_wysiwyg_action_starts_manual=false`、`current_wysiwyg_action_starts_keyboard=false`、`current_wysiwyg_action_starts_free_roam=false`、`current_wysiwyg_action_submits_delivery=false`、`current_wysiwyg_action_stops_motion=false`。
  - `HEAD http://127.0.0.1:7001/` 返回 `HTTP/1.1 200 OK`。
  - `HEAD http://127.0.0.1:7001/map` 返回 `HTTP/1.1 200 OK`。

## 剩余风险

- 本轮只暴露并绑定“当前所见只读动作”，不启动雷达 lifecycle、不启动建图、不发车。
- 当前真实 summary 仍显示 `camera_current_visible=false`、`radar_overlay_wysiwyg_complete=false`、`mapping_start_ready=false`；没有安全确认，也没有真实 Nav2/键盘/自由移动运动验收。
