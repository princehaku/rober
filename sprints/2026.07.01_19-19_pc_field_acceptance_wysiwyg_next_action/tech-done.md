# PC field acceptance WYSIWYG next action

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `field_acceptance_packet`，直接携带 WYSIWYG ready、缺口、主刷新端点、下一步文案、刷新顺序和 no-motion 刷新边界。
  - 扩展 summary 顶层 `field_acceptance_wysiwyg_*` alias，方便现场脚本一条 summary 读取当前所见下一步。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 从 `live_closure_summary` 透传相机、雷达贴图和 WYSIWYG 刷新合同到现场验收包。
  - 当相机和雷达点同时缺失时，把二者下一步合成普通用户可读的当前所见行动。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在 `plain-field-acceptance-packet` 顶部新增 `plain-field-acceptance-wysiwyg` 行，直接显示“当前所见”缺口和只读刷新按钮。
  - 刷新按钮复用 `refreshPlainWysiwygEvidence()`，只复测相机首帧、MJPEG 状态、雷达 scan proof、雷达状态和地图预览。
- `pc-tools/workstation/test/App.test.ts`
  - 增加现场验收包 WYSIWYG fixture、DOM 合同和点击 no-motion 断言。
- `docs/product/pc_tools_workstation.md`
  - 同步现场验收包当前所见 alias 和按钮行为合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - 通过：`Test Files 1 passed (1)`，`Tests 231 passed (231)`。
- `npm --prefix pc-tools/workstation run lint`
  - 通过：`eslint .` 无错误输出。
- `npm --prefix pc-tools/workstation run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
  - Vite 仍提示单 bundle 超过 500 kB，这是既有体积警告，不影响本轮合同。
- `npm --prefix pc-tools/workstation test -- --run`
  - 通过：`Test Files 3 passed (3)`，`Tests 421 passed (421)`。
- PC 7001 no-motion smoke
  - 已重启 PC 工作站到 `0.0.0.0:7001`，监听进程为 `node` PID `12223`。
  - `GET http://127.0.0.1:7001/` 返回 `200`。
  - `GET http://127.0.0.1:7001/map` 返回 `200`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `field_acceptance_wysiwyg_missing_surface_ids=["camera","radar_map_points"]`、`field_acceptance_wysiwyg_primary_refresh_endpoint=/api/robot-control/camera/first-frame/probe`、刷新顺序含 radar proof / camera probe / map preview / radar status / camera status，且 `field_acceptance_wysiwyg_refresh_sends_motion=false`、`field_acceptance_wysiwyg_refresh_starts_nav2=false`、`field_acceptance_wysiwyg_refresh_starts_manual=false`、`field_acceptance_wysiwyg_refresh_starts_keyboard=false`、`field_acceptance_wysiwyg_refresh_starts_free_roam=false`、`field_acceptance_wysiwyg_refresh_starts_radar_lifecycle=false`、`field_acceptance_wysiwyg_refresh_starts_map_runtime=false`、`field_acceptance_wysiwyg_refresh_submits_delivery=false`、`field_acceptance_wysiwyg_refresh_stops_motion=false`。
  - 当前 bundle `/assets/index-srEwETIq.js` 包含 `plain-field-acceptance-wysiwyg` 和 `data-wysiwyg-refresh-stops-motion`。

## 剩余风险

- 本轮不执行任何真实小车运动，不覆盖真实 HIL 发车链路。
- 本轮只做 no-motion summary/UI smoke；未点击真实 7001 页面里的刷新按钮，按钮行为由 Vitest fetch 断言覆盖。
