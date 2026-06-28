# PC 地图预览 Nav2 路线所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlMapPreviewResponse` 新增 `path_preview_points`、`path_preview_point_count`、`path_preview_source_point_count`、`path_preview_frame_id`、`path_preview_source_endpoint_ids`，让地图预览响应本身带出 Nav2 路线只读证据。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：`buildMapPreviewProxy` 复用固定只读 overlay readback，随地图图片返回 Nav2 路线点；失败响应也保持空路线字段，且不开放动态 endpoint、不调用任何控制接口。
- `pc-tools/workstation/test/catalog.test.ts`：扩展 map preview 代理测试，模拟 `/api/nav2/status` 带路线点，断言 PC 地图预览返回路线点和来源 endpoint，并继续确认未调用 `/api/nav2/goal/execute` 或 `/api/base/manual`。
- `docs/product/pc_tools_workstation.md`：同步说明地图预览路线字段只读合流口径。

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
  - `path_preview_source_point_count=18`
  - `path_preview_frame_id=map`
  - `path_preview_points.length=18`
  - `radar_overlay.overlay_status=not_current`，提示“已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。”
- 通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary`
  - `readback_summary.nav2.nav2_status=path_ready_with_service_blockers`
  - `readback_summary.nav2.path_preview_point_count=18`
  - `readback_summary.nav2.current_blocker_reasons=nav2_lifecycle_not_running`
  - `readback_summary.camera.status=source_first_frame_failed`
  - `readback_summary.camera.source_diagnosis_status=uvc_no_frame_not_exclusive`

## 剩余风险

- 本轮不发送真实 Nav2 goal、不做底盘运动验证；真实路线执行、wheel raw L/R 非零和 delivery success 仍需要现场安全确认后单独闭环。
