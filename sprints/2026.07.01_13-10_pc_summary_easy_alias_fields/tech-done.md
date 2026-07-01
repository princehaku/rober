# PC Summary 易读 Alias 字段

sprint_type: micro

## 实际改动

- `live_closure_summary` 新增普通脚本易读 alias：`nav2_route_ready`、`live_wysiwyg_camera_visible`、`live_wysiwyg_map_visible`、`primary_action_id`、`keyboard_continuous_ready`、`keyboard_continuous_motion_verified`、`keyboard_continuous_forwarded_pulses`。
- alias 均复用既有权威字段，不改变 PC 首屏状态机、不改变动作按钮、不新增任何运动入口。
- 同步 TypeScript contract、server summary、前端测试 fixture、summary 单测和产品文档。

## 验证结果

- 通过：`npm test -- --run test/robotControlSummary.test.ts -t "exposes minimal precheck fields for same-window wheel rerun"`，结果 `1 passed | 6 skipped`。
- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，结果 `1 passed | 230 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite build 成功；仍提示既有 chunk 大小 warning。
- 通过：`npm test`，结果 `3 passed` test files，`417 passed` tests。
- 通过：`git diff --check`。
- 通过：重启/自动拉起 `0.0.0.0:7001` 后只读验证 `GET /api/robot-control/summary`，`map_display_default_zoom_percent=400%`，`nav2_route_ready=true` 与 `route_ready_on_map=true`，`primary_action_id=run_nav2_route` 与 `live_motion_runbook_primary_action_id=run_nav2_route`，`keyboard_continuous_ready=true` 与 `keyboard_continuous_control_ready=true`。

## 剩余风险

- 本轮只改只读 summary 字段与测试合同；不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 工作区仍有两个历史 artifact 脏文件，本轮不纳入提交。
