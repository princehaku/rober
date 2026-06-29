# PC map preview 顶层下一步回到图上路线执行

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `GET /api/robot-control/map/preview` 的顶层 `next_action_plain` 改为镜像 `path_preview_next_action_plain`。
  - `map_wysiwyg_next_action_plain` 继续表达地图整体所见即所得缺口；当雷达未贴图时仍提示启动/刷新雷达。
  - `radar_overlay_next_action_plain` / `radar_overlay_wysiwyg_next_action_plain` 继续表达雷达贴图下一步。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 map preview 断言：顶层下一步等于路线下一步，而不是被雷达 overlay 缺口覆盖。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录顶层 `next_action_plain` 与路线执行下一步对齐，避免把雷达未贴图误解成 Nav2 发车前置。

## 验证结果

- `npm run build`：通过。
- `npm test -- catalog.test.ts`：通过，`167 passed`。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID 为 `21707`。
- live `GET http://127.0.0.1:7001/api/robot-control/map/preview`：
  - `proxy_status=preview_forwarded`
  - `robot_control_executed=false`
  - `robot_pose_status=map_pose_observed`
  - `path_preview_status=path_preview_observed`
  - `path_preview_point_count=18`
  - `next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`
  - `path_preview_next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`
  - `nav2_route_overlay_next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`
  - `map_wysiwyg_next_action_plain=先启动雷达并等待新扫描，再刷新地图画面确认雷达点。`
  - `radar_overlay_status=not_loaded`
  - `radar_overlay_next_action_plain=先启动雷达并等待新扫描，再刷新地图画面确认雷达点。`
- live equality check：
  - `next_action_plain == path_preview_next_action_plain` 为 `true`
  - `next_action_plain == nav2_route_overlay_next_action_plain` 为 `true`
  - `radar_overlay_next_action_plain` 仍包含“雷达”

## 剩余风险

- 本轮只修正 PC 只读字段别名，不执行 Nav2 goal、不启动雷达、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实完整 Nav2 路线执行和 wheel raw L/R 非零仍需要现场安全确认后重跑验证。
