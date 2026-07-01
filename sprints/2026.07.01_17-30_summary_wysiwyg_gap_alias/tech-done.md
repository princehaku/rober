# Summary WYSIWYG gap alias micro sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`GET /api/robot-control/summary` 顶层补齐 WYSIWYG 缺口、刷新计划、固定只读 endpoint、诊断文案和“不启动 runtime/不发运动”标志。
- `pc-tools/workstation/src/shared/contracts.ts`：同步新增顶层 WYSIWYG alias 类型，避免现场脚本读取 `live_wysiwyg_readback_gap_surface_ids` 等字段得到 `null`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：断言 summary 顶层字段与 `live_closure_summary` 同源，并保持只读边界。
- `docs/product/pc_tools_workstation.md`：记录当前 summary 顶层 WYSIWYG alias 合同。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，`9 passed`。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "live-summary"`，`1 passed | 180 skipped`。
- 已通过：`git diff --check`。
- 已通过：`cd pc-tools/workstation && npm test`，`421 passed`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。
- 已通过：重启 `0.0.0.0:7001`，当前监听 PID `98200`。
- 已通过：只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `live_wysiwyg_readback_gap_surface_ids=[]`、`live_wysiwyg_primary_readback_gap_surface_id=none`、`live_wysiwyg_missing_surface_refresh_endpoints=[/api/robot-control/camera/first-frame/probe,/api/robot-control/radar/scan-proof/refresh]`、`live_wysiwyg_refresh_sequence=[/api/robot-control/radar/scan-proof/refresh,/api/robot-control/camera/first-frame/probe,/api/robot-control/map/preview,/api/robot-control/radar/status,/api/robot-control/camera/mjpeg/status]`，且 `live_wysiwyg_refresh_starts_nav2/manual/keyboard/free_roam/radar_lifecycle/map_runtime=false`、`surface_count=3`。

## 剩余风险

- 本轮只修 summary 顶层只读字段，不打开相机、不启动雷达 lifecycle、不刷新地图、不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，也不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实 WYSIWYG 完成仍依赖现场相机首帧、当前地图雷达点贴图和后续硬件/运行验证；本轮交付的是现场脚本可直接读到准确缺口和只读恢复步骤。
