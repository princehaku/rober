# Free Roam Safe Boundary Split Micro Sprint

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 在 `safe_command_boundary` 顶层新增 `free_roam_motion_start_ready`、`free_roam_mapping_ready`、`free_roam_mapping_missing_reasons`。
  - 将“安全确认后可低速自由移动”和“相机/雷达/地图材料齐全，可按建图验收”拆成两个明确读数。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步扩展 `RobotControlSummaryResponse.safe_command_boundary` 合同。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 locked、start_ready、ready 三类 free-roam safe boundary。
- `pc-tools/workstation/test/App.test.ts`
  - 补齐默认 summary fixture 的新 safe boundary 字段。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录顶层 safe boundary 的自由移动/建图验收分层。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts --testNamePattern "free-roam|Robot Control summary keeps fixed control boundary"`
  - `Test Files 1 passed (1)`
  - `Tests 10 passed | 123 skipped (133)`
- 已通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 311 passed (311)`
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - Vite 保留既有 chunk size warning，构建成功。
- 已通过：`git diff --check`
- 已通过：重启 PC Node 到 `0.0.0.0:7001` 后只读 live summary 复查
  - `free_roam_autonomy=start_ready`
  - `free_roam_autonomy_start_ready=true`
  - `free_roam_motion_start_ready=true`
  - `free_roam_mapping_ready=false`
  - `free_roam_mapping_missing_reasons=["camera_first_frame","lidar_fresh","mapping_active","fresh_map_preview"]`
  - `free_roam_autonomy_label=自由移动（勾确认后可启动）`

## 剩余风险

- 本轮没有触发真实 free-roam start、manual、keyboard、Nav2 execute、delivery、stop 或 `/cmd_vel`。
- 当前 live 仍是 `free_roam_motion_start_ready=true` 但 `free_roam_mapping_ready=false`；摄像头首帧、地图记录、fresh map preview 等建图验收缺口仍未满足。
