# Safety-confirm Action Readback Aliases

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增安全确认后可执行动作的扁平 alias：`field_acceptance_safety_confirm_ready_action_stop_endpoints`、`field_acceptance_safety_confirm_ready_action_acceptance_endpoints`、`field_acceptance_safety_confirm_ready_action_minimal_precheck_safety_only`、`field_acceptance_safety_confirm_ready_action_camera_preflight_required`、`field_acceptance_safety_confirm_ready_action_radar_preflight_required`、`field_acceptance_safety_confirm_ready_action_route_wysiwyg_preflight_required`。
- primary safety action 同步新增单值 alias：stop endpoint、acceptance endpoints、minimal precheck 和 camera/radar/route WYSIWYG preflight flags。
- 普通首屏 `plain-field-acceptance-packet` DOM 同步暴露上述 `data-*`，现场无需解析 `safety_confirm_ready_actions[]` 就能确认勾安全确认后可执行什么、执行后读哪些端点。
- 更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，明确这些字段只描述安全确认后的执行/停止/读回口径，不自动勾确认、不发车、不提交送达、不 stop。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts robotControlSummary.test.ts`，结果 `2 passed (2)`、`246 passed (246)`。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`，生成 `dist/assets/index-DQC5TbW3.js`；Vite 仅保留既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001`，`lsof` 显示 `node ... TCP *:7001 (LISTEN)`。
- 通过：运行实例 summary 读到 safety-ready actions 为 `run_nav2_route, hold_keyboard, start_free_move`，primary 为 `run_nav2_route`，primary acceptance endpoints 为 `/api/robot-control/map/preview -> /api/robot-control/nav2/goal/execution/latest -> /api/robot-control/base/feedback-samples -> /api/robot-control/delivery/latest -> /api/robot-control/summary`。
- 通过：运行实例 summary 读到三项 safety-ready action 的 `minimal_precheck_safety_only=[true,true,true]`，`camera_preflight_required=[false,false,false]`，`radar_preflight_required=[false,false,false]`，`route_wysiwyg_preflight_required=[false,false,false]`。
- 通过：前端 bundle grep 到 `data-safety-confirm-ready-action-stop-endpoints`、`data-safety-confirm-ready-action-acceptance-endpoints`、`data-safety-confirm-ready-action-minimal-precheck-safety-only` 和 primary action 对应 DOM 字段。

## 剩余风险

- 本轮未获得新的现场安全确认，未发送 Nav2、keyboard、free-roam、mapping、delivery、stop 或 `/cmd_vel`；真实 wheel L/R 非零、delivery success、键盘运动闭环、自由移动运行和建图启动仍需现场安全确认后验证。
- 相机首帧仍未出，当前硬件方向仍是 USB full-speed / UVC 无帧；需要现场换高速 USB 口/线或带供电 Hub 后再复验。
