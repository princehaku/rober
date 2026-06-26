# 2026.06.27 06:11 Free Roam Policy Split

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：把 `safe_command_boundary.free_roam_autonomy_policy.mode` 从“需要上车 watchdog、雷达避障和 HIL”改为“自由移动需要安全确认和停止兜底”，并新增 `mapping_mode` / `mapping_required_gates`，把建图验收条件单独表达出来。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：Robot Control summary 固定边界同步输出新的分层 policy。这样 PC 首屏不会再把低速自由移动误解释成必须先满足雷达、地图和 free-roam HIL 全套条件。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：更新 fail-closed contract 和 UI fixture，确保自由移动 gate 与建图验收 gate 不再混在一起。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`：同步记录 2026-06-27 06:06 的 Nav2 wheel L/R 严格口径，以及 06:11 的自由移动/建图验收 policy 分层。

## 验证结果

- `npm test -- --run test/catalog.test.ts`：通过，`113 passed`。
- `npm test -- --run test/App.test.ts`：通过，`150 passed`。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `git diff --check`：通过。
- 重启 `0.0.0.0:7001` 后，用 live summary 确认
  `free_roam_autonomy_policy.mode=free_move_requires_safety_confirm_stop_fallback`、
  `mapping_mode=mapping_acceptance_requires_camera_and_fresh_radar`，移动 gate 为
  `operator_safety_confirmed/operator_stop_fallback`，建图 gate 为
  `camera_first_frame/fresh_radar_scan/map_recording_active/fresh_map_preview`。

## 剩余风险

- 本轮只修正 PC/API contract 和普通用户口径，不直接发车、不修改上车端运动控制，也不把当前真实小车状态宣称为已动。
- 当前现场 camera 仍需要上位机 `/dev/video*` 真实出帧链路复查；PC summary 已能区分不是浏览器独占 reader。
- 当前 Nav2 latest 仍是 `goal_succeeded` 但 wheel raw `L/R=0/0`，因此完整路线执行和 delivery success 仍不能验收为完成。
