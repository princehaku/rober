# Current Motion Action Alias

sprint_type: micro

## 实际改动

- 补齐 PC `GET /api/robot-control/summary` 顶层 `current_motion_action_*` 短字段，让现场脚本直接读取当前安全确认后动作、启动/停止端点、执行后读回端点、最小预检和传感器预检边界。
- 同步 TypeScript 合同、summary 单测和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：通过，3 个测试文件、428 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 保留既有 large chunk 提醒。
- `git diff --check`：通过。
- 已重启 PC Node，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` PID 62874 监听 `TCP *:7001`。
- 只读 smoke `GET http://127.0.0.1:7001/api/robot-control/summary`：`current_motion_action_id=run_nav2_route`、
  `current_motion_action_display_label=重跑图上行程并复验轮速`、start `/api/robot-control/nav2/goal/execute`、stop
  `/api/robot-control/base/stop`、acceptance endpoints 为 map preview、Nav2 latest、base feedback samples、delivery latest、summary；
  `current_motion_action_requires_safety_confirm=true`、`current_motion_action_minimal_precheck_safety_only=true`，
  相机/雷达/路线 WYSIWYG 预检均为 `false`。
- 重启后雷达贴图一度回到 `all_wysiwyg` 需刷新；按 no-motion WYSIWYG 序列重新刷新后，summary 显示
  `radar_overlay_status=loaded`、`radar_overlay_wysiwyg_complete=true`、当前地图雷达点 6 个，focused mode 回到 `camera_only`。
- `/map` HTTP smoke：`200 text/html; charset=utf-8`。

## 剩余风险

- 本轮没有新的现场安全确认，因此没有执行 Nav2、键盘 manual、free-roam、delivery complete、stop 或 `/cmd_vel`。
- 当前安全确认后主动作已明确为重跑图上行程并复验轮速，但 motion 仍缺同窗口 wheel L/R 非零和后续送达闭环。
- 相机仍报告 USB `12M` / `uvc_full_speed_usb_not_exclusive`，需要现场换高速 USB 后再复测；建图仍缺 `camera_first_frame`。
