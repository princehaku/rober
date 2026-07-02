# 四项目标审计缺口证据 alias

## sprint_type

micro

## 实际改动

- `objective_audit_items[]` 新增每项目标的机器可读缺口证据：
  - `missing_evidence_ids`
  - `missing_evidence_labels`
  - `readback_endpoints`
  - `next_action_requires_safety_confirm`
- 普通首屏 `plain-objective-overview-*` DOM 同步输出：
  - `data-missing-evidence-ids`
  - `data-missing-evidence-labels`
  - `data-readback-endpoints`
  - `data-next-action-requires-safety-confirm`
- 四项目标仍保持只读审计：按钮只聚焦到对应卡片，不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 更新 PC 工作站产品文档，明确现场脚本用这些字段判断当前缺口，不解析中文文案。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，`1 passed`。
- `npm test -- test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，`1 passed`。
- `npm test -- test/catalog.test.ts`：通过，`183 passed`。
- `npm run build`：通过，Vite 仅保留既有大 chunk 警告。
- `git diff --check`：通过。
- 已重启 PC 工作站到 `0.0.0.0:7001`。
- live summary 只读读回：
  - `objective_audit_status=in_progress`
  - `objective_audit_done_count=1`
  - `objective_audit_remaining_count=3`
  - `objective_audit_next_objective_id=motion`
  - `motion.missing_evidence_ids=same_window_wheel_lr_nonzero,delivery_success,keyboard_wheel_lr_nonzero,keyboard_stop_after_release,free_roam_motion_ready`
  - `wysiwyg.missing_evidence_ids=camera_first_frame`
  - `mapping.missing_evidence_ids=camera_first_frame`
  - `current_radar_map_wysiwyg_pack_status=loaded`
  - `current_radar_map_wysiwyg_pack_missing_evidence=[]`
- 雷达贴图 live 复核过程：
  - `POST /api/robot-control/radar/scan-proof/refresh` 返回 `readback_only=true`、`no_motion_refresh=true`、`robot_control_executed=false`、`latest_scan_proof_fresh=true`。
  - 第一轮 `GET /api/robot-control/map/preview` 仍为 `radar_overlay_status=not_current`，短延迟重读后恢复 `radar_overlay_status=loaded`、`radar_overlay_wysiwyg_complete=true`、当前地图雷达点 `147`、来源 `173`。

## 剩余风险

- 本轮只增强四项目标审计证据字段，没有发送运动命令。
- 真车完整 Nav2 行程、wheel raw L/R 非零、delivery success、键盘连续手控、自由移动和建图启动仍需要现场安全确认后的 HIL 验证。
- 当前 live 状态已知相机仍缺首帧，建图会继续被 `camera_first_frame` 阻塞；雷达地图贴图已 loaded。
- 工作区仍保留既有未纳入本轮的 artifact dirty 文件：
  - `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`
  - `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`
