# Mapping Start Gate Short Aliases

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- time: 2026-07-02 19:45 CST

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `mapping_start_gate_*` 顶层短字段，复用 `current_mapping_control_pack_*`，用于现场直接确认相机/雷达是否都 ready、谁阻塞建图、建图启动/停止/预览端点、启动后只读复验顺序，以及建图缺口是否阻塞自由移动。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐 `RobotControlSummaryResponse` 的 `mapping_start_gate_*` 可选字段类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 PC `plain-current-mapping-control-pack` 同步暴露 `data-mapping-start-gate-*` DOM 合同。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 summary 字段与 DOM 属性。
- `docs/product/pc_tools_workstation.md`：同步说明建图门禁短别名、点击不启动建图 runtime、相机和雷达 ready 后才可现场安全确认执行建图。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，1 个测试文件、10 个用例通过。
- 通过：`npm test -- test/App.test.ts`，1 个测试文件、237 个用例通过。
- 通过：`npm run build`，TypeScript 与 Vite build 成功；仅保留既有 Vite chunk size 警告。
- 通过：`git diff --check`，无空白错误。
- 通过：重启 PC workstation 到 `0.0.0.0:7001` 后只读调用 `GET /api/robot-control/summary`，读到
  `readback_only=true`、`robot_control_executed=false`、`mapping_start_gate_status=blocked`、
  `mapping_start_gate_is_ready=false`、`mapping_start_gate_camera_required=true`、
  `mapping_start_gate_radar_required=true`、`mapping_start_gate_camera_blocks_start=true`、
  `mapping_start_gate_sends_motion_when_clicked=false`、`mapping_start_gate_starts_map_runtime_when_clicked=false`、
  `mapping_start_gate_starts_map_runtime_when_executed=true`。
- 通过：只读执行 `POST /api/robot-control/radar/scan-proof/refresh` 后回包保持
  `safe_to_control=false`、`robot_control_executed=false`、`starts_radar_lifecycle=false`、
  `starts_nav2=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`stops_motion=false`。
  随后 summary 显示 `radar_map_wysiwyg_status=loaded`、`live_wysiwyg_status=only_camera_hardware_action`、
  `mapping_start_gate_radar_ready=true`、`mapping_start_gate_missing_evidence_labels=[画面首帧]`、
  `mapping_start_gate_radar_overlay_wysiwyg_complete=true`、`mapping_start_gate_free_move_allowed_while_blocked=true`。

## 剩余风险

- 当前改动只补 PC/API 可读合同与前端 DOM，不替代真实建图启动验收。
- 真车建图仍必须等相机首帧和雷达新鲜读数都 ready，并在现场安全确认后启动。
- 当前实机状态仍可能因为相机首帧或雷达贴图读回缺口而阻塞建图；自由移动仍可按安全确认先做。
