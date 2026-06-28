# PC map preview top-level next action

## sprint_type

micro

## 实际改动

- 在 `RobotControlMapPreviewResponse` 中新增顶层 `next_action_plain`，与 `path_preview_next_action_plain` 对齐。
- `/api/robot-control/map/preview` 成功和 fail-closed 分支都返回同一个图上路线下一步，避免外部脚本只读统一字段时拿到空值。
- PC fallback、测试 fixture、合同测试、`pc-tools/README.md` 和 `docs/product/pc_free_roam_mapping_design.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map preview"`
  - `Test Files 1 passed (1)`
  - `Tests 2 passed | 156 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍有既有 chunk size warning，但 build 成功。
- 通过：本机 7001 只读 live map preview 验证。
  - 7001 监听为 workstation 的 `tsx src/server/index.ts` / `node` 进程，未触碰 Clash。
  - `curl http://127.0.0.1:7001/api/robot-control/map/preview` 返回：
    `proxy_status=preview_forwarded`、`status=loaded_fail_closed_summary`、
    `path_preview_status=path_preview_observed`、
    `path_preview_next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`、
    `next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`、
    `path_preview_point_count=18`、`path_preview_frame_id=map`、
    `robot_pose_status=map_pose_observed`、`radar_overlay_status=not_current`、
    `radar_overlay_next_action_plain=先启动雷达，再刷新地图画面。`、
    `robot_control_executed=false`。

## 剩余风险

- 本轮只补只读 map preview alias；雷达贴图下一步仍使用独立 `radar_overlay_next_action_plain`。
- 未获得本轮现场安全确认前，不做真实 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel` 验证。
