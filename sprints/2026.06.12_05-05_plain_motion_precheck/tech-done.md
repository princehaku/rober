# 2026-06-12 05:05 Plain Motion Precheck

## sprint_type

micro

## 功能设计

目标：把“移动前先完成画面、轮子和周围环境检查”的普通首屏提示推进成一个可操作入口，但不能绕过现有非 stop 运动门禁。

普通用户首屏新增 `移动前检查`：

- 位置：`Rober 小车控制台` 的 `移动/导航` 卡片，和 `重新定位`、`停止` 放在同一普通动作区。
- 文案：普通用户语言，只显示 `检查中 / 已记录 / 检查失败` 和短提示。
- 提交内容：只提交 `operator_present=true`、`physical_clearance_confirmed=true`、`emergency_stop_ready=true`、`observed_stop=true`、`site_state=plain_motion_precheck_ready_for_review`、短 `evidence_ref` 和 notes。
- 不提交内容：不提交 `external_video_recorded`、`visible_content_proven`、`wheel_feedback_lr_nonzero_proven`、`physical_motion_lidar_delta_proven`、`real_route_map_proven`、`delivery_success`。
- 安全结果：提交后应刷新 summary；由于关键材料仍缺，`operatorMaterialReady` 必须继续为 false，非 stop 手动移动按钮仍禁用，真实 `/api/base/manual` 不能被调用。
- 高级诊断：保留完整 operator report 表单，不移除已有字段；普通首屏不显示 `operator_report`、HIL、proof、endpoint、raw/readback。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通 `.simple-user-console` 的 `移动/导航` 卡片新增 `移动前检查` 按钮。
  - 新增 `plainMotionPrecheckRequestBody()`，只提交 `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`、`observed_stop`、`site_state` 和普通 evidence ref。
  - 普通预检查显式保持 `external_video_recorded=false`、`visible_content_proven=false`、`wheel_feedback_lr_nonzero_proven=false`、`physical_motion_lidar_delta_proven=false`、`real_route_map_proven=false`、`delivery_success=false`。
  - 普通首屏只显示 `检查中 / 已记录 / 检查失败`，不显示 `operator_report`、HIL、proof、endpoint、raw/readback。
- `pc-tools/workstation/test/App.test.ts`
  - 首屏 contract 增加 `移动前检查`。
  - 新增普通预检查回归：验证请求 body 不含顶层 `safe_to_control/delivery_success`，四类关键运动材料不被置 true，且不会调用 `/api/base/manual`。
- `docs/product/pc_tools_workstation.md`
  - 将 `移动前检查` 纳入普通首屏允许动作，并明确它不能替代真实运动材料。
- `docs/navigation/fixed_route_workflow.md`
  - 记录普通预检查的 no-motion / no-base-control 边界和 manual reject 证据。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 记录本轮未操作 UART/ESP32/GPIO，manual forward 仍被 gate 拒绝。

## 验证结果

- `cd pc-tools/workstation && npm run test -- App.test.ts`
  - 1 file passed, 18 tests passed.
- 真实 PC proxy 普通预检查：
  - request artifact: `artifacts/01_plain_motion_precheck_request.json`
  - response artifact: `artifacts/02_pc_proxy_plain_motion_precheck_response.json`
  - `proxy_status=report_forwarded`
  - `remote_http_status=200`
  - `rejected_fields=[]`
  - `hard_dangerous_true_fields=[]`
- PC summary readback：
  - artifact: `artifacts/03_pc_summary_after_plain_motion_precheck.json`
  - `operator_present=true`
  - `physical_clearance=true`
  - `emergency_stop=true`
  - `external_video=false; ref=not_loaded`
  - `camera_visible=false; ref=not_loaded`
  - `wheel_feedback=false; ref=not_loaded`
  - `lidar_delta=false; ref=not_loaded`
- Manual forward gate：
  - request artifact: `artifacts/04_manual_forward_reject_request.json`
  - response artifact: `artifacts/05_pc_manual_forward_reject_response.json`
  - HTTP artifact: `artifacts/05_pc_manual_forward_reject_http_status.txt`
  - HTTP 400
  - `proxy_status=command_rejected`
  - `failure_reason=operator_report_preflight_required`
  - `remote_http_status=null`
  - `robot_control_executed=false`
  - missing fields include external video/ref、visible camera/ref、wheel feedback/ref、scan delta/ref.
- Browser DOM smoke：
  - artifact: `artifacts/06_browser_plain_motion_precheck_dom.json`
  - `.simple-user-console` has enabled `移动前检查`、`重新定位`、`停止`.
  - 默认高级诊断未展开。
  - 普通首屏未出现 `operator_report`、`structured_hil_claims`、`external_video_recorded`、`physical_motion_lidar_delta_proven`、HIL、proof、`/cmd_vel`、`/api/base/manual`、速度、时长、点动。

## 剩余风险

- 本轮不证明真实移动；它证明普通预检查不会绕过非 stop motion gate。
- 手动移动仍缺外部视频、可见图传、左右轮非零反馈和 LiDAR motion delta 材料。
- 相机 `/dev/video1` 首帧 timeout 与地图 `free=0` blocker 仍未解决。
