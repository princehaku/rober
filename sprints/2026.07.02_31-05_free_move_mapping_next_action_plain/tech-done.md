# Free Move And Mapping Next Action Plain

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：为当前自由移动控制包和建图控制包补齐 `*_next_action_plain`，让 summary 直接说明下一步。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐共享类型字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-current-free-move-control-pack`、`plain-current-mapping-control-pack` 同步暴露 `data-next-action-plain`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 API 和 DOM 合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录下一步白话字段边界。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts test/App.test.ts`，`Test Files 2 passed (2)`，`Tests 247 passed (247)`。
- 通过：`npm run build`，TypeScript app/server 与 Vite build 均完成；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001` 后 live 读取 summary，`current_free_move_control_pack_next_action_plain=勾现场安全确认后启动自由自助移动；启动后只读读取 free-roam latest、地图预览和 summary。`。
- 通过：重启后先读到雷达贴图待刷新，随后按 no-motion 链路执行 `POST /api/robot-control/radar/scan-proof/refresh`、`GET /api/robot-control/radar/status`、`GET /api/robot-control/map/preview`；scan proof 返回 `readback_only=true`、`no_motion_refresh=true`、`starts_radar_lifecycle=false`、`starts_nav2=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`stops_motion=false`，radar status 返回 `radar_overlay_wysiwyg_complete=true`。
- 通过：最终 live summary 返回 `live_wysiwyg_missing_surface_ids=["camera"]`、`radar_overlay_status=loaded`、`radar_overlay_wysiwyg_complete=true`、`current_mapping_control_pack_only_camera_missing=true`、`current_mapping_control_pack_blocks_free_move=false`，建图下一步为相机 USB full-speed 硬件处理后复测。

## 剩余风险

- 本轮只补只读 API/DOM 易用性，不发送真实运动指令。
- 当前 live 目标仍需要现场安全确认后的 Nav2/键盘/自由移动 HIL 证据，以及相机 USB/full-speed blocker 处理后复测首帧。
