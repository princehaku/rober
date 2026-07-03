# PC summary map WYSIWYG aliases

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 将当前地图画面的关键实时事实抬到 `GET /api/robot-control/summary` 顶层：`map_preview_status`、`path_preview_point_count`、`route_target_visible`、`route_target_source`、`route_target_state`、`robot_pose_status`。
  - `map_preview_status` 在当前地图画面已可见时返回 `loaded`，避免旧 map proof 的 `not_proven` 误导现场脚本。
- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/live-summary` 复用 summary 顶层 `map_preview_status`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐这些 summary 顶层 alias 的 TypeScript 合同。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 锁定顶层 alias 与 `readback_summary.map` 同源。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC summary 顶层地图 WYSIWYG alias 契约。

## 验证结果

- `npm test -- test/robotControlSummary.test.ts -t "camera"`：3 passed。
- `npm test -- test/catalog.test.ts -t "map preview"`：4 passed。
- `npm run build`：通过。
- 重启 PC Node 后，`0.0.0.0:7001` 正常监听。
- Live `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回：
  - `map_preview_status=loaded`
  - `map_current_visible=true`
  - `path_current_visible=true`
  - `path_preview_point_count=18`
  - `route_target_visible=true`
  - `route_target_source=path_preview_points`
  - `route_target_state=path_preview_goal_observed`
  - `robot_pose_status=map_pose_observed`
  - `radar_overlay_status=loaded`
  - `radar_overlay_current_point_count=43`

## 剩余风险

- 这轮只修 summary 顶层读回一致性，不改变真实相机无首帧状态；当前相机仍为 `uvc_no_frame_not_exclusive`，需要检查摄像头输入/线/供电或换 known-good UVC 复测。
- `path_preview_point_count` 在 summary 顶层按既有合同保持字符串，与 map preview endpoint 的数字值同源但类型不同。
