# Tech Done

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增并固定只读边界：`readback_only=true`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`sends_motion_when_clicked=false`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`submits_delivery=false` 和 `stops_motion=false`。
- `GET /api/robot-control/live-summary` 顶层补齐 `robot_control_executed=false`，与既有 no-motion flags 对齐。
- 更新共享契约、summary/live-summary builder、回归测试和产品文档，避免现场 `curl | jq` 把 summary/live-summary 缺失字段读成 `null` 后误判只读总览可能会发车或发布 `/cmd_vel`。

## 验证结果

- `npm test -- test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，`1 passed`。
- `npm test -- test/catalog.test.ts`：通过，`183 passed`。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过，无空白错误。
- 已重启 PC 服务到 `0.0.0.0:7001`，进程 PID `92753`。
- Live 只读复验：
  - `GET /api/robot-control/summary` 返回 `readback_only=true`、`robot_control_executed=false`、`publishes_cmd_vel=false`、同组动作边界均为 `false`。
  - `GET /api/robot-control/live-summary` 返回 `readback_only=true`、`robot_control_executed=false`、`publishes_cmd_vel=false`、同组动作边界均为 `false`。
  - 重启后雷达贴图曾短暂 stale；执行固定 no-motion `POST /api/robot-control/radar/scan-proof/refresh` 与 `GET /api/robot-control/map/preview` 后，summary 回到 `live_wysiwyg_missing_surface_ids=["camera"]`、`radar_overlay_wysiwyg_complete=true`。

## 剩余风险

- 相机真实首帧仍未恢复，当前 live 缺口为 `camera_first_frame`，原因仍是 USB 12M / `first_frame_total_timeout`。
- 完整 Nav2、键盘连续手控、自由移动和 delivery success 仍需要现场安全确认后的真实 HIL 证据；本轮没有发送任何运动指令。
