# PC summary 地图下一步字段对齐

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`readback_summary.map` 增加两个顶层别名：
  - `next_action_plain`：等于 `path_preview_next_action_plain`，表达图上路线/小车位置的下一步。
  - `map_next_action_plain`：等于 `map_wysiwyg_next_action_plain`，表达整张地图所见即所得的下一步。
- `pc-tools/workstation/src/shared/contracts.ts`：同步固定 summary map response contract。
- `pc-tools/workstation/test/catalog.test.ts`：补充 summary map 顶层下一步与 path/map WYSIWYG 字段的对齐断言，覆盖无路线、雷达已贴图、旧雷达点不贴图场景。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录 summary 与直连 map preview 的下一步字段分层口径。

## 验证结果

- `npm run build`：通过。
- `npm test -- catalog.test.ts`：通过，`167 passed`。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `git diff --check`：通过。
- 重启 PC Node：`HOST=0.0.0.0 PORT=7001 ROBOT_CONTROL_DEFAULT_BASE_URL=http://192.168.1.11:8787 npm run api`，监听 `*:7001`，PID `48610`。
- live 只读验证 `GET http://127.0.0.1:7001/api/robot-control/summary`：
  - `readback_summary.map.next_action_plain=图上路线和小车位置已显示；确认起点、终点和路线后，再勾选安全确认执行。`
  - `readback_summary.map.map_next_action_plain=先启动雷达并等待新扫描，再刷新地图画面确认雷达点。`
  - `path_preview_status=path_preview_observed`
  - `path_preview_point_count=18`
  - `robot_pose_status=map_pose_observed`
  - `radar_overlay_status=not_loaded`
  - `radar_overlay_point_count=0`
- live 只读验证 `GET http://127.0.0.1:7001/api/robot-control/map/preview`：同一组 next action 字段与 summary 对齐，且 `robot_control_executed=false`。

## 剩余风险

- 本轮只补 summary 只读字段，不执行 Nav2、不启动雷达、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 当前 live 仍显示雷达 overlay 未加载；路线和小车位置已所见即所得，但雷达开始后的地图标记仍要等雷达运行并产生新扫描后验证。
- 摄像头仍无首帧；自由移动可先做，但建图验收还缺相机首帧和雷达新鲜扫描。
