# PC 自由移动验收条

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通自由移动卡新增 `plain-free-move-acceptance-proof` 只读验收条。
  - 验收条优先消费 summary 顶层 `free_move_*` alias，并兼容旧 `live_motion_runbook_items.start_free_move`。
  - DOM 明确暴露自由移动 start/stop endpoint、验收读回端点、proof status、缺失证据、最小预检、相机/雷达不作为移动前置、建图缺口，以及完整 no-motion 读回边界。
- `pc-tools/workstation/test/App.test.ts`
  - 默认 summary fixture 补齐自由移动验收 alias。
  - 在“相机未出帧但自由移动可先做”场景锁定验收条文案和 DOM 合同。
- `docs/product/pc_tools_workstation.md`
  - 记录 `plain-free-move-acceptance-proof` 产品边界：它只解释自由移动验收缺口，不替代真实启动按钮和现场安全确认。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts -t "allows free-roam recording when camera source is selected but not yet frame-proven"`，1 passed / 232 skipped。
- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`，233 passed。
- 已通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`，190 passed。
- 已通过：`git diff --check`。
- 已通过：`npm --prefix pc-tools/workstation run lint`。
- 已通过：`npm --prefix pc-tools/workstation run build`；Vite 仍保留既有 chunk size warning。
- 已通过：`npm --prefix pc-tools/workstation test -- --run`，423 passed。
- 已通过：PC Node 已后台重启到 `0.0.0.0:7001`，监听 PID `29489`；`GET /map` 返回 `200`。
- 已通过：只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `free_move_ready=true`、`free_move_proof_status=ready_to_verify`、`free_move_missing_evidence=["free_roam_latest_motion_ready"]`、`free_move_start_endpoint=/api/robot-control/free-roam/autonomy/start`、`free_move_acceptance_endpoints=[/api/robot-control/free-roam/autonomy/latest,/api/robot-control/summary]`、`free_move_minimal_precheck_safety_only=true`、`free_move_camera_preflight_required=false`、`free_move_radar_preflight_required=false`、`mapping_start_ready=false`、`mapping_start_missing_reasons=["camera_first_frame"]`、`map_display_default_zoom_percent=1000%`。

## 剩余风险

- 本轮只补 PC 普通界面自由移动验收读回展示，不发送自由移动 start、Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 自由移动真实完成仍需要现场勾安全确认后启动，并读回 `/api/robot-control/free-roam/autonomy/latest` 与 summary，确认 `free_roam_latest_motion_ready`。
- 当前完整目标仍未收口：Nav2 完整路线同窗口 wheel L/R 非零、delivery success、键盘连续手控 wheel L/R 非零、相机首帧和自由移动运行态还需要现场材料。
