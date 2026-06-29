# PC map preview 雷达无当前点不再误报 partial

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 修正 `buildMapPreviewOverlayReadback` 的 `radar_overlay_status` 判定。
  - `partial` 现在只用于“有当前雷达点但缺少 map pose 等贴图材料”；只有小车位置但没有当前雷达点时不再返回 partial。
  - 雷达无当前点时返回 `not_loaded`；有旧来源点但雷达 stale/stopped 时返回 `not_current`，当前贴图点数仍为 0。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 map preview 测试，覆盖“map pose 存在但雷达无当前点”的 live 形态。
  - 保留既有“有雷达点但无 map pose 返回 partial”和“stopped/stale 旧点不贴图”测试。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录直连 map preview 与 summary 对齐的地图雷达 WYSIWYG 判定。

## 验证结果

- `npm run build`：通过。
- `npm test -- catalog.test.ts`：通过，`167 passed`。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`。
- live `curl http://127.0.0.1:7001/api/robot-control/map/preview`：
  - `proxy_status=preview_forwarded`
  - `radar_overlay_status=not_loaded`
  - `radar_overlay_point_count=0`
  - `robot_pose_status=map_pose_observed`
  - `path_preview_status=path_preview_observed`
  - `radar_overlay_next_action_plain=先启动雷达并等待新扫描，再刷新地图画面确认雷达点。`
- live `curl http://127.0.0.1:7001/api/robot-control/summary`：
  - `readback_summary.map.radar_overlay_status=not_loaded`
  - `readback_summary.map.radar_overlay_point_count=0`
  - `readback_summary.map.radar_overlay_wysiwyg_next_action_plain=先启动雷达并等待新扫描，再刷新地图画面确认雷达点。`

## 剩余风险

- 本轮只修正只读地图预览状态判定，不启动雷达、不刷新雷达、不执行真实运动。
- live 上雷达仍未运行，地图雷达当前点仍为 0；需要现场启动雷达并刷新地图画面后才能证明雷达点贴图。
