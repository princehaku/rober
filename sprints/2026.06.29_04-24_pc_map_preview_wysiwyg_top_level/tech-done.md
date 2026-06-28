# PC Map Preview WYSIWYG Top Level

sprint_type: micro

## 实际改动

- `/api/robot-control/map/preview` 顶层新增地图所见即所得总口径：
  - `map_wysiwyg_status_plain`
  - `map_wysiwyg_next_action_plain`
- 同一响应新增图上路线/路径的普通别名：
  - `path_wysiwyg_status_plain`
  - `path_wysiwyg_next_action_plain`
  - `nav2_route_overlay_status`
  - `nav2_route_overlay_point_count`
  - `nav2_route_overlay_next_action_plain`
- 成功、failed、blocked 分支都返回这些字段。地图画面未通过当前只读代理验证时，不会宣称地图所见即所得。
- PC 前端 fallback、App fixture、catalog map preview 测试、README 和产品文档已同步。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map preview"`
  - `Test Files 1 passed (1)`
  - `Tests 2 passed | 158 skipped (160)`
- 已通过：`npm --prefix pc-tools/workstation run build`
  - TypeScript、Vite client build、server TypeScript 均通过。
  - Vite 仍有既有 chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 375 passed (375)`
- 已重启 PC workstation API 到 `0.0.0.0:7001`，监听进程为 `node`。
- 已通过：只读验证 `/api/robot-control/map/preview` 顶层新字段。
  - `proxy_status=preview_forwarded`
  - `robot_control_executed=false`
  - `map_wysiwyg_status_plain=地图画面、图上路线和小车位置已显示；雷达来源点存在但当前不贴到地图：已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。`
  - `map_wysiwyg_next_action_plain=先启动雷达，再刷新地图画面。`
  - `path_preview_status=path_preview_observed`
  - `path_preview_point_count=18`
  - `path_wysiwyg_status_plain=图上路线已显示在当前地图画面。`
  - `nav2_route_overlay_status=path_preview_observed`
  - `nav2_route_overlay_point_count=18`
  - `nav2_route_overlay_next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`
  - `robot_pose_status=map_pose_observed`
  - `radar_overlay_status=not_current`
  - `radar_overlay_point_count=0`
  - `radar_overlay_source_point_count=81`
  - `radar_overlay_wysiwyg_status_plain=雷达 marker 未贴到当前地图：当前显示 0 个点；旧来源点 81 个只作诊断。已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。`

## 剩余风险

- 本轮只补只读 map preview 合同，不启动雷达、不准备或执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 未获得本轮现场安全确认前，不做真实运动、键盘连续手控、自由移动或自动驾驶执行验证。
