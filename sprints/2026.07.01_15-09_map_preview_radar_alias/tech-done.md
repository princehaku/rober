# Map Preview Radar Alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`GET /api/robot-control/map/preview` 顶层补齐雷达贴图恢复 alias，包括是否需要刷新、是否阻塞 WYSIWYG、是否不阻塞自由移动、恢复顺序和固定只读端点。
- `pc-tools/workstation/src/shared/contracts.ts`：同步 `RobotControlMapPreviewResponse` 字段。
- `pc-tools/workstation/test/catalog.test.ts`：扩展 stale radar overlay 测试，锁定旧雷达点不贴图时 `radar_overlay_blocks_wysiwyg=true` 且 `radar_overlay_blocks_free_move=false`。
- `docs/product/pc_tools_workstation.md`：记录 `/api/robot-control/map/preview` 顶层 radar overlay alias 与 no-motion 边界。

## 验证结果

- 通过：`npm test -- --run test/catalog.test.ts -t "map preview radar overlay does not draw stopped stale radar points"`，1 passed。
- 通过：`npm test`，3 files / 421 tests passed。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：PC Node 已重启到 `0.0.0.0:7001`，新 PID `91264`。
- 通过：只读 curl `/api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=preview_forwarded`、`radar_overlay_status=not_current`、`radar_overlay_source_point_count=181`、`radar_overlay_primary_blocked_reason=runtime_scan_stale_for_map_radar_overlay`、`radar_overlay_needs_refresh=true`、`radar_overlay_blocks_wysiwyg=true`、`radar_overlay_blocks_free_move=false`、`radar_overlay_recovery_sequence=[/api/robot-control/radar/scan-proof/refresh,/api/robot-control/map/preview]`、`radar_overlay_refresh_sends_motion=false`、`radar_overlay_refresh_starts_radar_lifecycle=false`、`robot_control_executed=false`、`hard_dangerous_true_fields=[]`。

## 剩余风险

- 本轮只补 map preview 只读合同，不自动刷新雷达、不启动雷达 lifecycle、不启动自由移动或建图 runtime，也不触发 Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 完整目标仍未收口：相机首帧、同窗口 wheel L/R 非零、delivery success、键盘连续手控和自由移动运行态仍需现场材料。
