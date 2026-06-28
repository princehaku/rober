# PC Summary Map WYSIWYG Short Aliases

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `readback_summary.map` 增加 `robot_pose_status`、`radar_overlay_point_count`、`radar_overlay_source_point_count` 和 `radar_overlay_frame_id`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：短别名完全复用既有 `radar_overlay_robot_pose_status` 与 `radar_overlay_scan_preview_*` 事实；当前雷达 overlay 不贴图时，point count 继续是 `0`，source count 保留诊断来源点。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补齐默认夹具和三类 map/radar overlay 回归断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录只读 summary alias。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map|radar overlay|WYSIWYG|path_preview|robot_pose"`：通过，1 个文件，17 个测试通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个文件，373 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 保留既有 chunk size warning。
- 7001 本地 live 只读复验：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `readback_summary.map.robot_pose_status=map_pose_observed`、`radar_overlay_status=not_current`、`radar_overlay_point_count=0`、`radar_overlay_source_point_count=81`、`radar_overlay_frame_id=laser_frame`，且短别名与既有长字段一致；`safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补 PC 只读 alias，不启动雷达、不刷新地图、不发车，不证明现场雷达 marker 已当前贴图。
- 当前 live 仍显示雷达来源点存在但扫描过期/雷达未运行，所以 `radar_overlay_point_count` 应保持 `0`，不能把旧来源点当作地图 marker。
