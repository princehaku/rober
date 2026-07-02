# 2026-07-02 08:16 CST current motion action PC UI

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainCurrentMotionActionGauge`，普通 PC 行程区优先消费 summary 顶层 `current_motion_action_*` 字段。
  - `plain-trip-current-motion-action` 新增普通可见短行，直接说明当前运动动作、只需安全确认、执行后读回端点数量。
  - `plain-trip-closure-gate`、`plain-trip-execute`、`plain-trip-execution-gauge` 同步暴露 `data-current-motion-action-*`，便于现场脚本不用解析嵌套包即可确认完整 Nav2 行程动作。
- `pc-tools/workstation/test/App.test.ts`
  - 补齐 summary fixture 的 `current_motion_action_*` 字段。
  - 覆盖门禁、执行按钮、行程仪表和新增短行的 DOM 合同。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通 PC 行程区消费 `current_motion_action_*` 的产品边界。

## 验证结果

- `npm test -- --run App.test.ts`
  - 通过：`Test Files 1 passed (1)`，`Tests 237 passed (237)`。
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
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`，PID `29132`。
- 只读 smoke：
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 通过，读到 `current_motion_action_id=run_nav2_route`、`current_motion_action_display_label=重跑图上行程并复验轮速`、`current_motion_action_start_endpoint=/api/robot-control/nav2/goal/execute`、`current_motion_action_stop_endpoint=/api/robot-control/base/stop`、`current_motion_action_acceptance_endpoints=[map preview, nav2 latest, base feedback samples, delivery latest, summary]`、`current_motion_action_minimal_precheck_safety_only=true`、`current_motion_action_camera_preflight_required=false`、`current_motion_action_radar_preflight_required=false`、`current_motion_action_route_wysiwyg_preflight_required=false`。
  - `HEAD http://127.0.0.1:7001/` 返回 `HTTP/1.1 200 OK`。
  - `HEAD http://127.0.0.1:7001/map` 返回 `HTTP/1.1 200 OK`。

## 剩余风险

- 本轮只做 PC UI/DOM 绑定，不发送运动请求；没有安全确认，也没有真实 Nav2 发车、wheel L/R 非零或 delivery success 现场证据。
- 本轮只读 summary 仍显示 `camera_current_visible=false`、`radar_overlay_wysiwyg_complete=false`、`mapping_start_ready=false`，因此画面、雷达贴图和建图 ready 目标未完成。
- 本轮不宣称完整目标完成，下一步仍需在安全确认后执行真实 Nav2/键盘/自由移动动作并读回同窗口 wheel L/R、delivery success、相机首帧和雷达贴图。
