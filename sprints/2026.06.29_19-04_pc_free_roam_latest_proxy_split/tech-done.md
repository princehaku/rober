# 2026.06.29 19:04 PC free-roam latest proxy split

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `GET /api/robot-control/free-roam/autonomy/latest` 的 `latest_key_values` 现在收录 `free_roam_motion_start_ready`、`motion_without_radar_allowed`、`free_move_without_camera_allowed`、`free_roam_mapping_start_ready`、`free_roam_mapping_start_missing_reasons`、`free_roam_mapping_start_plain` 和 `free_roam_mapping_start_next_action`。
  - PC 代理把上车 `camera_first_frame_not_observed/radar_scan_proof_not_fresh` 归一为 PC summary 使用的 `camera_first_frame/lidar_fresh`。
  - 成功响应顶层显式返回 `sends_commands=false`、`sends_motion_commands=false`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlFreeRoamAutonomyLatestResponse` 的自由移动/建图启动字段。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 free-roam latest fixture，锁定 PC 代理与 summary 的同一套分层字段。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 PC 代理与上车 latest/summary 对齐后的 WYSIWYG 口径。

## 验证结果

- 已通过：`npm run build`（`pc-tools/workstation`）
  - 结果：TypeScript app/server build 与 Vite build 通过；仅保留既有 chunk-size warning。
- 已通过：`npm test -- App.test.ts`（`pc-tools/workstation`）
  - 结果：`Test Files 1 passed (1)`，`Tests 218 passed (218)`。
- 已通过：`git diff --check`
- 已重启本机 PC Node：
  - `HOST=0.0.0.0 PORT=7001 npm run api`
  - live `GET http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/latest` 摘要：
    `motion_start_ready=true`、`motion_without_radar_allowed=true`、`free_move_without_camera_allowed=true`、
    `mapping_start_ready=false`、`mapping_start_missing=[camera_first_frame,lidar_fresh]`、
    `latest_key_values.free_roam_mapping_start_ready=false`、`sends_motion_commands=false`

## 剩余风险

- 本轮只修 PC 只读代理字段，不实际启动自由移动或建图。
- live 相机仍无首帧、雷达仍未 fresh；因此建图启动继续保持 not ready，但低速自由移动/键盘手控口径保持可在安全确认后启动。
