# Free Move Readback Single Aliases

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增 `free_move_readback_endpoint`、`free_move_latest_endpoint` 和 `free_move_required_success_marker` 顶层 summary alias。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 alias 与既有 `free_move_readback_endpoints` / `free_move_required_success_markers` 同源，单值 endpoint 固定为 `/api/robot-control/free-roam/autonomy/latest`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 motion proof DOM 补 `data-free-move-readback-endpoint`、`data-free-move-required-success-marker` 和 `data-free-move-required-success-markers`。
- 同步更新 `App.test.ts`、`robotControlSummary.test.ts`、`pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；保留既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `17755`。
- 真实 summary 只读 smoke 返回 `free_move_start_ready=true`、`free_roam_motion_ready=false`、`free_move_readback_endpoint=/api/robot-control/free-roam/autonomy/latest`、`free_move_latest_endpoint=/api/robot-control/free-roam/autonomy/latest`、`free_move_readback_endpoints=[/api/robot-control/free-roam/autonomy/latest,/api/robot-control/map/preview,/api/robot-control/summary]`、`free_move_required_success_marker=free_roam_latest_motion_ready`、`free_move_required_success_markers=[free_roam_latest_motion_ready]`。
- 重启后雷达贴图一度 stale，按已声明 no-motion 链路执行 `radar scan proof -> radar status -> map preview -> summary` 后恢复为 `live_wysiwyg_missing_surface_ids=[camera]`、`radar_overlay_wysiwyg_complete=true`、`radar_map_points_visible=true`。refresh 回包证明 `readback_only=true`、`no_motion_refresh=true`、所有 `starts_*`、`submits_delivery`、`stops_motion` 和 `robot_control_executed` 均为 false。

## 剩余风险

- 本轮未发任何运动/control POST，未启动 free-roam、Nav2、键盘、建图或 delivery complete。
- 真实 motion 目标仍缺安全确认后的完整 Nav2 路线同窗口 wheel raw L/R 非零、delivery success、PC 键盘连续手控和自由移动运行读回。
- 当前 WYSIWYG 和建图启动仍只剩相机首帧硬件缺口。
