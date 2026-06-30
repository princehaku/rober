# PC Map Preview Embedded Radar Overlay

- sprint_type: micro
- owner: Codex mainline (subagent disabled per CEO instruction)
- time: 2026-07-01 07:38 CST

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `GET /api/robot-control/map/preview` 现在优先采用上车 `/api/map/preview` 随图返回的 `radar_overlay` 作为当前地图雷达层证据。
  - `GET /api/robot-control/summary` 增加只读 `/api/map/preview` readback，并同样优先采用上车 map preview 内嵌 overlay，避免首屏 summary 和 `/map` 大屏对同一轮地图雷达点给出相反结论。
  - 上车 map preview 没有 `radar_overlay` 或显式 `radar_overlay_status` 时，继续 fallback 到既有 radar/status、scan-proof、定位/Nav2 readback 合成 overlay。
  - 只接受 `loaded|partial|blocked|not_current|not_loaded` 五种已知 overlay 状态；普通地图 `status=loaded` 不会被误当成雷达 overlay loaded。
- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotApiReadEndpointId` 增加 `map_preview`，用于标记 overlay 证据来源。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加回归测试：当上车 map preview 自带 loaded radar overlay、旁路 scan proof 暂时 stale 时，PC map preview 必须返回 loaded/current。
- `docs/product/pc_tools_workstation.md`
  - 同步地图预览 WYSIWYG 合同：地图本体 overlay 优先，旁路 readback 只做兜底。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts`
  - 通过：`Test Files 1 passed (1)`，`Tests 7 passed (7)`。
- `npm test -- --run test/catalog.test.ts -t "Robot Control summary|radar.*overlay|map preview|scan-proof"`
  - 通过：`Test Files 1 passed (1)`，`Tests 49 passed | 130 skipped (179)`。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；仍保留既有 Vite chunk size warning。
- `npm test`
  - 通过：`Test Files 3 passed (3)`，`Tests 416 passed (416)`。
- `git diff --check`
  - 通过。
- PC 服务重启验证
  - 已重启 `npm run api`，监听 `http://0.0.0.0:7001`，PID `57922`。
- 现场只读 map preview / summary 一致性验证
  - `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=133`、`radar_overlay_source_point_count=138`、`radar_overlay_source_endpoint_ids=["map_preview"]`、`robot_control_executed=false`、`safe_to_control=false`。
  - `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `summary_radar_overlay_status=loaded`、`summary_radar_overlay_point_count=133`、`summary_radar_overlay_source_point_count=138`、`summary_radar_overlay_refresh_required=false`。
  - `live_wysiwyg_missing_surface_ids=["camera"]`，说明地图和雷达点 WYSIWYG 已对齐，当前仍缺相机画面。

## 剩余风险

- 本轮只修地图预览和 summary 的只读 overlay 口径，没有执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- `readback_summary.map.status` 仍保留 map proof 的原始 `not_proven` 状态；普通首屏 WYSIWYG 以 `map_current_visible=true`、`radar_overlay_status=loaded` 和 live surface summaries 为准。
- 目标仍未完成：相机首帧仍失败，诊断为 `uvc_full_speed_usb_not_exclusive`；完整运动闭环还缺现场安全确认后的同窗口 wheel L/R 非零复验和 delivery success。
