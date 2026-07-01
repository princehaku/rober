# Keyboard Post-hold Readback Aliases

## sprint_type

micro

## 实际改动

- 在 `RobotControlSummaryResponse` 顶层补充键盘松开/停止后的只读复验 alias：`fixed_keyboard_feedback_readback_endpoint`、`fixed_keyboard_summary_endpoint`、`keyboard_post_hold_readback_endpoints`、`keyboard_post_hold_readback_sequence_labels`、`keyboard_post_hold_feedback_readback_required` 和 `keyboard_post_hold_summary_refresh_required`。
- `buildRobotControlSummary()` 复用 `live_closure_summary.fixed_keyboard_*` 与 post-hold required 字段输出上述 alias，避免现场脚本再解析嵌套 live closure。
- 普通首屏 `plain-live-closure-summary` DOM 同步暴露 `data-keyboard-post-hold-*`，用于验收 key release / stop 后必须读取 wheel feedback samples 再刷新 summary。
- 更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，明确该链路只读，不发送 manual pulse、stop、Nav2/free-roam/建图/delivery 或 `/cmd_vel`。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts robotControlSummary.test.ts`，结果 `2 passed (2)`、`246 passed (246)`。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`，生成 `dist/assets/index-DoB1O1BG.js`；Vite 仅保留既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001`，`lsof` 显示 `node ... TCP *:7001 (LISTEN)`。
- 通过：`curl http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 读到 `keyboard_post_hold_readback_endpoints=["/api/robot-control/base/feedback-samples","/api/robot-control/summary"]`、`keyboard_post_hold_readback_sequence_labels=["复验键盘轮速采样","刷新总览"]`、`keyboard_post_hold_feedback_readback_required=true`、`keyboard_post_hold_summary_refresh_required=true`。
- 通过：前端 bundle grep 到 `data-keyboard-post-hold-readback-endpoints`、`data-keyboard-post-hold-readback-sequence-labels`、`data-keyboard-post-hold-feedback-readback-required`、`data-keyboard-post-hold-summary-refresh-required`。
- 通过：同次 summary 核对地图口径仍为 `map_display_primary_url=/map`、`map_display_default_zoom_percent=1600%`、`map_display_ros2_companion_tools=["rviz2","foxglove"]`、`map_display_ros2_companion_required=false`。

## 剩余风险

- 本轮不发送任何运动控制 POST，未做真实键盘按住让车移动的 HIL 验收；真实 wheel raw L/R 非零仍需要 CEO 现场安全确认后执行。
- 当前地图太小/ROS2 配套口径沿用既有 `/map` 大地图 + RViz2/Foxglove 工程观察合同，本轮只核对不重做地图 UI。
