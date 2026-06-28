# sprint_type: micro

## 实际改动

- `/api/robot-control/map/preview` 新增顶层雷达 overlay alias：
  - `radar_overlay_status`
  - `radar_overlay_plain_hint`
  - `radar_overlay_next_action`
  - `radar_overlay_points`
  - `radar_overlay_count`
  - `radar_overlay_source_count`
  - `radar_overlay_frame_id`
- 顶层 alias 全部从同一份 `radar_overlay` 嵌套对象派生，避免地图画面里“当前贴图点数”和 curl/jq 一眼读数不一致。
- stopped/stale 雷达场景继续保持所见即所得：旧雷达来源点只进入 `source_count` 和中文说明，`count=0`、`points=[]`，不会被当成当前地图点。
- 只改只读 map preview 响应合同和测试，不触发雷达启动、手控、Nav2 或任何运动命令。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "map preview radar overlay"`：通过，4 passed。
- `npm --prefix pc-tools/workstation test`：通过，366 passed。
- `npm --prefix pc-tools/workstation run build`：通过，Vite 仍提示现有 chunk 大于 500 kB 的非阻塞 warning。
- `git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/robotControlSummary.ts pc-tools/workstation/test/catalog.test.ts`：通过。
- 已重启 PC Node 到 `0.0.0.0:7001`，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node PID 73837 监听 `*:7001`。
- 只读 live `GET /api/robot-control/map/preview`：顶层返回 `radar_overlay_status=not_current`、`radar_overlay_count=0`、`radar_overlay_source_count=81`、`radar_overlay_frame_id=laser_frame`、`radar_overlay_points=0`，嵌套 `radar_overlay.count/source_count/frame_id` 与顶层一致，`robot_control_executed=false`。
- 只读 live `GET /api/robot-control/summary`：Nav2 仍显示上次路线 action 成功但 `wheel raw L/R=0/0`，自由移动仍显示勾安全确认后可先移动，`robot_control_executed=false`。

## 剩余风险

- 本轮只修复 map preview 响应的一眼读法；没有启动雷达刷新，所以 live 仍是旧雷达来源点 81 个、当前地图贴图点 0 个。
- 没有现场安全确认，本轮没有执行自由移动、键盘手控、Nav2 重跑或送达确认；完整目标仍未完成。
