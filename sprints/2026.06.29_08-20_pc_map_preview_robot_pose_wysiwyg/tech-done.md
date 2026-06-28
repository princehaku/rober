# PC 地图预览顶层小车位置所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlMapPreviewResponse` 新增顶层 `robot_pose` 字段，类型为 `RobotApiMapPose | null`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：`buildMapPreviewProxy` 将同一轮只读 overlay readback 的 `radar_overlay.robot_pose` 提升到顶层 `robot_pose`，失败响应保持 `null`，不新增任何控制 endpoint。
- `pc-tools/workstation/test/catalog.test.ts`：扩展 map preview 代理测试，断言顶层 `robot_pose` 与 `radar_overlay.robot_pose` 一致，且继续保持 `robot_control_executed=false`。
- `docs/product/pc_tools_workstation.md`：同步说明 map preview 单次响应同时带地图图片、路线、小车位置和雷达贴图状态。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files  2 passed (2)`
  - `Tests  365 passed (365)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
  - 仍有既有 Vite chunk size warning：`dist/assets/index-*.js` 大于 500 kB；本轮未扩大处理范围。
- 通过：重启 7001 后读取 `GET http://127.0.0.1:7001/api/robot-control/map/preview`
  - `proxy_status=preview_forwarded`
  - `robot_control_executed=false`
  - `path_preview_point_count=18`
  - `path_preview_frame_id=map`
  - 顶层 `robot_pose={x:-0.0045,y:0.0091,yaw:0.0055,frame_id:map,source:/amcl_pose}`
  - `radar_overlay.robot_pose` 与顶层 `robot_pose` 一致。
  - `radar_overlay.overlay_status=not_current`，继续说明“已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。”
- 通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary`
  - `readback_summary.free_roam.status=start_ready`
  - `safe_command_boundary.keyboard_control_start_ready=true`
  - `readback_summary.nav2.path_preview_point_count=18`
  - `readback_summary.camera.status=source_first_frame_failed`

## 剩余风险

- 本轮只提升只读地图预览合同，不发送定位 reset、Nav2 goal、manual、keyboard、free-roam start、delivery、stop 或 `/cmd_vel`。真实路线执行、键盘连续控制 HIL、wheel raw L/R 非零和 delivery success 仍需现场安全确认后单独闭环。
