# PC map radar overlay plain hint WYSIWYG

## sprint_type

micro

## 实际改动

- `RobotControlMapPreviewRadarOverlay` 新增 `plain_hint`、`next_action`、`blocked_reason_labels`，把雷达点是否贴到地图、为什么不贴图、下一步动作从内部 token 变成可直接展示的字段。
- `readback_summary.map` 同步新增 `radar_overlay_plain_hint`、`radar_overlay_next_action`、`radar_overlay_blocked_reason_labels`，summary 与 `/api/robot-control/map/preview` 共用同一套归因。
- live 形态“已有旧雷达来源点，但雷达 lifecycle 停止或 /scan 过期”会显示为“已有雷达来源点，但雷达扫描已过期/雷达未运行，所以当前不贴到地图”，而不是只暴露 `runtime_scan_stale_for_map_radar_overlay` 这类内部 token。
- 普通首屏地图/雷达事实优先消费 `radar_overlay_plain_hint`，旧 PC Node 没有该字段时才回退到原来的点数文案。
- 更新 catalog/App 测试，覆盖 loaded、partial、not_current 三种 radar overlay 状态。
- 更新 `docs/product/pc_tools_workstation.md`，记录该变化只读地图/雷达/定位材料，不发送任何运动命令。

## 验证结果

- `npm --prefix pc-tools/workstation test` 通过：2 个 test files、365 个 tests 全部通过。
- `npm --prefix pc-tools/workstation run build` 通过：`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` 全部完成；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提示。
- PC Node 已按 `HOST=0.0.0.0 PORT=7001 npm --prefix pc-tools/workstation run api` 重启，`lsof` 确认 PID `38423` 监听 `*:7001`。
- 只读复核 `GET http://127.0.0.1:7001/api/robot-control/summary`：`radar_overlay_status=not_current`、`radar_overlay_plain_hint=已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。`、`radar_overlay_next_action=start_radar_then_refresh_map_preview`、`radar_overlay_blocked_reason_labels=雷达扫描已过期,雷达未运行`、`robot_control_executed=false`。
- 只读复核 `GET http://127.0.0.1:7001/api/robot-control/map/preview`：`radar_overlay.overlay_status=not_current`、`plain_hint=已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。`、`scan_preview_point_count=0`、`scan_preview_source_point_count=81`、`blocked_reason_labels=[雷达扫描已过期,雷达未运行]`、`robot_control_executed=false`。

## 剩余风险

- 该轮只改善地图雷达 overlay 的所见即所得说明，不启动雷达、不刷新真实 /scan、不执行 Nav2 或键盘运动。
- live 当前仍显示雷达 lifecycle stopped、相机无首帧，因此建图验收仍不 ready；自由移动/键盘/Nav2 路线 gate 仍需要现场安全确认后分别操作。
