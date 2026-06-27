# Map Preview Radar Overlay Readback

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增 `RobotControlMapPreviewRadarOverlay`，并让地图预览响应可携带只读 `radar_overlay`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：`/api/robot-control/map/preview` 转发地图图片时，并发读取固定定位/Nav2/雷达 endpoint，聚合雷达预览点、小车地图位姿和 overlay 读数状态；overlay 失败不阻塞地图图片。
- `pc-tools/workstation/test/catalog.test.ts`：覆盖地图预览代理返回图片、雷达点和小车位姿，且仍只命中固定 GET 读接口、不执行控制。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录地图预览响应现在具备图片、雷达点和位姿的同轮只读材料。

## 验证结果

- `npm test -- test/catalog.test.ts --testNamePattern "workstation map lifecycle proxies"`：通过。
- `npm test -- test/catalog.test.ts`：通过，132 个测试通过。
- `npm test -- test/App.test.ts --testNamePattern "map|radar"`：通过，61 个相关测试通过。
- `npm test`：通过，309 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍提示单 chunk 超过 500 kB，这是既有前端构建体积提示，不影响本次合同变更。
- `git diff --check`：通过。
- live 读回 `http://127.0.0.1:7001/api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787`：`preview_forwarded`，地图图像 `223x116`，`radar_overlay.overlay_status=loaded`，`scan_preview_point_count=65`，`scan_preview_frame_id=laser_frame`，`robot_pose.source=/amcl_pose`。

## 剩余风险

- 本轮只修 PC map preview 合同层的所见即所得材料聚合，不触发真实底盘运动、不 rerun Nav2 goal、不修复摄像头无首帧硬件问题。
- `radar_overlay` 字段对旧前端 fixture 保持可选兼容；真实 Node 代理路径会返回该字段。
