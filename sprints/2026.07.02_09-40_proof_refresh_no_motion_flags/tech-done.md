# 2026.07.02 09:40 proof refresh no-motion flags

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlProofRefreshProxyResponse` 新增 proof refresh 本体 no-motion 合同字段：`readback_only`、`no_motion_refresh`、`sends_motion_when_clicked`、`starts_*`、`submits_delivery`、`stops_motion`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：三个固定 proof refresh POST 代理和错误兜底统一返回上述 no-motion 字段，避免现场 `curl` 读到 `null` 后还要跳 summary 证明不会发车。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：浏览器侧 proof refresh fallback 同步补齐 no-motion 字段。
- `pc-tools/workstation/test/catalog.test.ts`：补 radar/map/nav2 proof refresh 回包 no-motion 字段断言。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步 proof refresh 回包合同。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 files passed，427 tests passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单 chunk 超 500 kB 的既有警告。
- 重启 PC Node：`0.0.0.0:7001` 已监听，PID `35941`。
- 实机只读/no-motion smoke：
  - `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=refresh_forwarded`、`readback_only=true`、`no_motion_refresh=true`、所有 `starts_*`/`sends_motion_when_clicked`/`submits_delivery`/`stops_motion=false`、`robot_control_executed=false`。
  - `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=155`、`radar_overlay_source_point_count=185`、`radar_overlay_refresh_required=false`。
  - `GET /api/robot-control/summary` 返回 `live_wysiwyg_missing_reasons=["camera"]`、`radar_overlay_wysiwyg_complete=true`、`radar_map_points_visible=true`、`live_wysiwyg_only_camera_missing=true`、`mapping_start_only_camera_missing=true`。

## 剩余风险

- 完整目标仍未完成：当前 `objective_missing_ids=["motion","wysiwyg","mapping"]`。
- Motion 仍需显式安全确认后的真实验收：完整 Nav2 路线同窗口 wheel raw L/R 非零、delivery success、PC 键盘连续手控轮速非零和松开停稳、自由移动运行读回。
- Camera 仍是当前唯一 WYSIWYG blocker：`camera_wysiwyg_recovery_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`，需要换高速 USB/供电 Hub 或 known-good UVC 后复测 `camera_first_frame`。
- 建图仍缺 `camera_first_frame`；雷达贴图和雷达新鲜读回本轮已通过 no-motion smoke，但不能替代相机 ready。
