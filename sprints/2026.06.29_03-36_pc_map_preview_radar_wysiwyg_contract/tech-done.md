# PC Map Preview Radar WYSIWYG Contract

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `RobotControlMapPreviewRadarOverlay` 增加 `wysiwyg_status_plain` 和 `wysiwyg_next_action_plain`，并在 `RobotControlMapPreviewResponse` 增加顶层 `radar_overlay_wysiwyg_status_plain` 和 `radar_overlay_wysiwyg_next_action_plain` alias。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：让 `/api/robot-control/map/preview` 的 nested overlay、blocked/default overlay 和顶层 alias 都返回雷达贴图 WYSIWYG 白话。
- `pc-tools/workstation/test/catalog.test.ts`：补充 map preview partial 与 not_current overlay 的 nested/top-level WYSIWYG 断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录 map preview endpoint 的只读合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "map preview radar overlay"`：通过，1 个文件，2 个测试通过，156 个跳过。
- `npm --prefix pc-tools/workstation test`：通过，2 个文件，373 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 保留既有 chunk size warning。
- 7001 本地 live 只读复验：`GET http://127.0.0.1:7001/api/robot-control/map/preview` 返回 `proxy_status=preview_forwarded`、`radar_overlay.status=not_current`、nested/top-level WYSIWYG 均为 `雷达 marker 未贴到当前地图：当前显示 0 个点；旧来源点 81 个只作诊断。已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。`，`radar_overlay_count=0`、`radar_overlay_source_count=81`、`robot_pose_status=map_pose_observed`、`path_preview_status=path_preview_observed`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补 `/api/robot-control/map/preview` 的只读响应合同，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- live 自动驾驶仍需现场安全确认后重跑图上路线并确认同窗口 wheel raw L/R 非零；本轮未触发任何运动命令。
