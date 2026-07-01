# PC 安全确认后运动验收动作清单

sprint_type: micro

## 实际改动

- `field_acceptance_packet` 新增 `safety_confirm_ready_actions[]`，把“勾安全确认后可执行”的运动验收从 ID 清单升级为结构化动作。
- 每个动作暴露：
  - 普通用户 label。
  - 固定 start/stop/readback endpoint。
  - `requires_safety_confirm=true`。
  - `minimal_precheck_safety_only=true`。
  - `camera_preflight_required=false`、`radar_preflight_required=false`、`operator_report_preflight_required=false`、`route_wysiwyg_preflight_required=false`。
  - 实际会启动的类型：Nav2 / manual+keyboard / free-roam / map runtime。
- `GET /api/robot-control/summary` 顶层同步暴露 `field_acceptance_safety_confirm_ready_action_*` 与 `field_acceptance_primary_safety_confirm_ready_action_*`。
- 普通首屏 `plain-field-acceptance-packet` 和 `plain-field-acceptance-remaining-actions` 同步暴露 labels、start endpoints 和 primary 字段。
- `pc-tools/README.md` 同步记录该合同和最小预检边界。

## 验证结果

- 已通过：`npm test -- robotControlSummary.test.ts App.test.ts`
  - 结果：`Test Files 2 passed (2)`，`Tests 245 passed (245)`。
- 已通过：`npm run build`
  - 结果：TypeScript app/server 和 Vite production build 通过；仅保留既有 chunk size warning。
- 已通过：`git diff --check`
  - 结果：无 whitespace error。
- 已通过：后台重启 Node 工作站并读取真实 `GET /api/robot-control/summary`
  - 监听：`0.0.0.0:7001`，PID `81375`。
  - 小车地址：`http://192.168.1.11:8787`。
  - 结果：`status=needs_wheel_rerun`，`live_wysiwyg_missing_surface_ids=["camera"]`，`radar_overlay_status=loaded`。
  - 结果：`field_acceptance_safety_confirm_ready_step_ids=["run_nav2_route","hold_keyboard","start_free_move"]`。
  - 结果：labels 为 `["完整行程执行","键盘连续手控","自由自助移动"]`。
  - 结果：start endpoints 为 `["/api/robot-control/nav2/goal/execute","/api/robot-control/base/manual","/api/robot-control/free-roam/autonomy/start"]`。
  - 结果：primary 为 `run_nav2_route` / `完整行程执行` / `/api/robot-control/nav2/goal/execute`，`requires_safety_confirm=true`，`sends_motion=true`。
  - 结果：三项动作均 `minimal_precheck_safety_only=true`，`camera/radar/route_wysiwyg_preflight_required=false`；分别标明启动 Nav2、manual+keyboard、free-roam。

## 剩余风险

- 该改动只暴露动作合同，不自动勾安全确认，不自动执行 Nav2、键盘、自由移动或建图。
- 当前真实小车仍需现场安全确认后执行运动项，才能收口 wheel L/R 非零、delivery success 和键盘连续手控。
