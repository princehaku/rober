# PC map WYSIWYG summary plain

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary.readback_summary.map` 新增：
  - `map_wysiwyg_status_plain`
  - `map_wysiwyg_next_action_plain`
- 新字段把地图底图、图上路线、小车 map 位置和雷达 overlay 合成一个普通用户可读总判断。
- 当雷达 proof 里有旧来源点，但 runtime `/scan` 已过期或雷达 lifecycle stopped 时，总状态会明确写“雷达来源点存在但当前不贴到地图”，避免脚本把旧点当作当前 marker。
- `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map overlay|Robot Control summary"`
  - `Test Files 1 passed (1)`
  - `Tests 38 passed | 120 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仅输出 chunk size warning，构建成功。
- 通过：7001 只读 summary 验证。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001 (LISTEN)`。
  - `GET /api/robot-control/summary` 返回 `map_wysiwyg_status_plain=地图画面、图上路线和小车位置已显示；雷达来源点存在但当前不贴到地图：已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。`
  - 同一响应显示 `path_preview_status=path_preview_observed`、`path_preview_point_count=18`、`radar_overlay_status=not_current`、`radar_overlay_scan_preview_point_count=0`、`radar_overlay_scan_preview_source_point_count=81`、`radar_overlay_robot_pose_status=map_pose_observed`。
  - `safe_to_control=false`，`robot_control_executed=false`，确认本轮验证未执行真实控制动作。

## 剩余风险

- 本轮只补只读 map summary 字段，不启动雷达、不刷新地图、不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 未获得本轮现场安全确认前，不做真实路线执行、自由移动或键盘脉冲 HIL 验证。
