# 最小发车预检缺口 alias

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 新增：
  - `current_minimal_precheck_pack_missing_evidence`
  - `current_minimal_precheck_pack_missing_evidence_labels`
- 当最小预检已经收敛到 `safety_confirm_only` 或运动验收完成时返回空数组 `[]`，不再让现场脚本读到 `null`。
- 当最小预检仍 blocked 时，字段列出未收敛的额外前置：相机、雷达、现场报告、路线 WYSIWYG 或“只需安全确认未证明”。
- 普通首屏 `plain-current-minimal-precheck-pack` 同步暴露 `data-missing-evidence` 与 `data-missing-evidence-labels`，空数组显示为 `none`。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，`1 passed`。
- `npm test -- test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，`1 passed`。
- `npm test -- test/catalog.test.ts`：通过，`183 passed`。
- `npm run build`：通过，Vite 仅保留既有大 chunk 警告。
- `git diff --check`：通过。
- 已重启 PC 工作站到 `0.0.0.0:7001`。
- live summary 只读读回：
  - `current_minimal_precheck_pack_status=safety_confirm_only`
  - `current_minimal_precheck_pack_missing_evidence=[]`
  - `current_minimal_precheck_pack_missing_evidence_labels=[]`
  - `current_minimal_precheck_pack_safety_confirm_required=true`
  - `current_minimal_precheck_pack_minimal_precheck_safety_only=true`
  - `current_minimal_precheck_pack_camera_preflight_required=false`
  - `current_minimal_precheck_pack_radar_preflight_required=false`
  - `current_minimal_precheck_pack_operator_report_preflight_required=false`
  - `current_minimal_precheck_pack_route_wysiwyg_preflight_required=false`
  - `current_trip_execution_pack_status=ready_for_safety_confirm`
  - `current_keyboard_control_pack_status=ready_for_safety_confirm`
  - `current_free_move_control_pack_status=ready_for_safety_confirm`
  - `current_mapping_control_pack_status=blocked`
  - `current_camera_wysiwyg_pack_status=needs_first_frame`
  - `current_radar_map_wysiwyg_pack_status=loaded`

## 剩余风险

- 本轮只补最小预检只读缺口字段，不发送运动命令。
- 当前真实状态仍需现场安全确认后验证 Nav2/键盘/自由移动；相机首帧仍需现场换高速 USB 后复测。
