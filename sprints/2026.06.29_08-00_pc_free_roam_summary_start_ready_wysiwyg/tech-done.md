# PC 自由移动摘要 start_ready 所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`readback_summary.free_roam.status` 不再直接沿用上车端 artifact 的原始 `not_proven/loaded`，而是按 PC 可执行语义派生为 `start_ready`、`motion_ready` 或 `mapping_ready`。原始 runtime 信息继续保留在 `runtime_status`、`decision_state`、`artifact_only` 和 `cmd_vel_publish_enabled`。
- `pc-tools/workstation/test/catalog.test.ts`：补充并调整自由移动 summary 断言，覆盖“可启动但未发布运动”、“运动发布中但建图材料未齐”和“建图材料齐全”三种状态。
- `docs/product/pc_tools_workstation.md`：同步记录自由移动 summary 状态派生口径。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files  2 passed (2)`
  - `Tests  365 passed (365)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
  - 仍有既有 Vite chunk size warning：`dist/assets/index-*.js` 大于 500 kB；本轮未扩大处理范围。
- 通过：重启 7001 后读取 `GET http://127.0.0.1:7001/api/robot-control/summary`
  - `readback_summary.free_roam.status=start_ready`
  - `readback_summary.free_roam.runtime_status=loaded`
  - `readback_summary.free_roam.cmd_vel_publish_enabled=false`
  - `readback_summary.free_roam.start_ready=true`
  - `readback_summary.free_roam.motion_start_ready=true`
  - `readback_summary.free_roam.mapping_ready=false`
  - `safe_command_boundary.free_roam_autonomy=start_ready`
  - `safe_command_boundary.free_roam_autonomy_label=自由移动（勾确认后可启动）`
- 通过：只读 `GET http://127.0.0.1:7001/api/robot-control/map/preview`
  - `proxy_status=preview_forwarded`
  - `robot_control_executed=false`
  - `path_preview_point_count=18`
  - `radar_overlay.overlay_status=not_current`

## 剩余风险

- 本轮不发送 `free-roam/autonomy/start`，不做真实自由移动 HIL；真实低速自助移动、wheel raw L/R 非零、完整 Nav2 路线执行和 delivery success 仍需现场安全确认后单独闭环。
