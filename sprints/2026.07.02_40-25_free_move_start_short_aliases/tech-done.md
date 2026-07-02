# Free Move Start Short Aliases

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- time: 2026-07-02 19:25 CST

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `free_move_start_*` 顶层短字段，复用 `current_free_move_control_pack_*`，用于现场直接确认自由自助移动可启动、只需安全确认、启动后只读复验，以及建图仍缺的传感器证据。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐 `RobotControlSummaryResponse` 的 `free_move_start_*` 可选字段类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 PC `plain-current-free-move-control-pack` 同步暴露 `data-free-move-start-*` DOM 合同。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 summary 字段与 DOM 属性。
- `docs/product/pc_tools_workstation.md`：同步说明自由移动短别名、点击不发车、现场安全确认后启动 free-roam、启动后只读复验，以及相机/雷达只影响建图。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，1 个测试文件、10 个用例通过。
- 通过：`npm test -- test/App.test.ts`，1 个测试文件、237 个用例通过。
- 通过：`npm run build`，TypeScript 与 Vite build 成功；仅保留既有 Vite chunk size 警告。
- 通过：`git diff --check`，无空白错误。
- 通过：重启 PC workstation 到 `0.0.0.0:7001` 后只读调用 `GET /api/robot-control/summary`，读到
  `readback_only=true`、`robot_control_executed=false`、`free_move_start_status=ready_for_safety_confirm`、
  `free_move_start_is_ready=true`、`free_move_start_requires_safety_confirm=true`、
  `free_move_start_camera_preflight_required=false`、`free_move_start_radar_preflight_required=false`、
  `free_move_start_mapping_start_ready=false`、`free_move_start_mapping_start_missing_reasons=[camera_first_frame]`、
  `free_move_start_sends_motion_when_clicked=false`、`free_move_start_sends_motion_when_executed=true`、
  `free_move_start_starts_free_roam_when_clicked=false`、`free_move_start_starts_free_roam_when_executed=true`。

## 剩余风险

- 当前改动只补 PC/API 可读合同与前端 DOM，不替代真实 free-roam 发车验收。
- 真车自由移动仍需要现场勾安全确认后启动，并复验 `free_roam_latest_motion_ready`。
- 建图仍必须等相机和雷达 ready；自由移动短别名不会绕过建图传感器条件。
