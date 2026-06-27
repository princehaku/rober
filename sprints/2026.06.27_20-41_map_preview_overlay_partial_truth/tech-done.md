# Map Preview Overlay Partial Truth Micro Sprint

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 收紧 `/api/robot-control/map/preview.radar_overlay.overlay_status`：只有雷达点和 map-frame 机器人位姿同时存在才是 `loaded`。
  - 有雷达点但缺 `robot_pose` 时返回 `partial`，并写入 `robot_pose_missing_for_map_radar_overlay`，避免 PC 地图把局部雷达点冒充成已贴地图。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 live-like 回归：地图图像和雷达点存在、定位只有 TF 信号无 map pose 时，overlay 必须是 `partial`，且不调用 Nav2 execute、manual 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录完整 overlay 和 partial overlay 的所见即所得边界。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts --testNamePattern "map preview radar overlay"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 132 skipped (133)`
- 已通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 311 passed (311)`
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - Vite 保留既有 chunk size warning，构建成功。
- 已通过：`git diff --check`
- 已通过：重启 PC Node 到 `0.0.0.0:7001` 后只读 live map preview 复查
  - `proxy_status=preview_forwarded`
  - 真实地图图片存在，尺寸 `223x116`
  - `radar_overlay.overlay_status=partial`
  - `scan_preview_point_count=65`
  - `radar_overlay.robot_pose=null`
  - `blocked_reasons=["robot_pose_missing_for_map_radar_overlay"]`

## 剩余风险

- 本轮没有触发真实定位重置、雷达启动、Nav2 execute、manual、keyboard、free-roam start、delivery、stop 或 `/cmd_vel`。
- 当前 live 定位仍缺 map-frame `robot_pose`，因此雷达点只能按局部轮廓/点数解释，不能按已贴地图坐标收口。
- 摄像头仍是 UVC 无首帧且非页面独占；完整可验收建图仍需要相机首帧和雷达/地图/定位同时 ready。
