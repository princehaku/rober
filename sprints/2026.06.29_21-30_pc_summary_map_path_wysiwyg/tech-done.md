# PC summary map path WYSIWYG

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 的 `readback_summary.map` 新增图上路线 WYSIWYG 字段：
  `path_preview_status`、`path_preview_point_count`、`path_preview_frame_id`、`path_preview_next_action_plain`。
- summary map 区块现在能同时表达地图质量、图上路线、雷达贴图和小车 map 位姿状态；外部脚本不用再从 nav2 区块手动拼路线点数。
- fail-closed summary、前端 fixture、合同测试、`pc-tools/README.md` 和 `docs/product/pc_free_roam_mapping_design.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "summary"`
  - `Test Files 1 passed (1)`
  - `Tests 44 passed | 114 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍有既有 chunk size warning，但 build 成功。
- 通过：本机 7001 只读 live summary 验证。
  - 7001 监听为 workstation 的 `tsx src/server/index.ts` / `node` 进程，未触碰 Clash。
  - `curl http://127.0.0.1:7001/api/robot-control/summary` 返回：
    `readback_summary.map.status=map_once_artifact_metadata_observed`、
    `map_quality_status=has_free_cells`、`map_free_cell_count=421`、
    `path_preview_status=path_preview_observed`、
    `path_preview_point_count=18`、`path_preview_frame_id=map`、
    `path_preview_next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`、
    `radar_overlay_status=not_current`、
    `radar_overlay_next_action_plain=先启动雷达，再刷新地图画面。`、
    `radar_overlay_robot_pose_status=map_pose_observed`、
    `safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补只读 summary 字段，不准备路线、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 未获得本轮现场安全确认前，不做真实运动或自动驾驶执行验证。
