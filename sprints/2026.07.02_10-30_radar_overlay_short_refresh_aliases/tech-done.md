# Radar Overlay Short Refresh Aliases

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增雷达贴图短 alias：
  - `radar_overlay_next_action_plain`
  - `radar_overlay_refresh_sequence`
  - `radar_overlay_refresh_sequence_labels`
- 这些字段分别与 `radar_overlay_refresh_next_action_plain`、`radar_overlay_recovery_sequence`、`live_wysiwyg_radar_map_refresh_sequence_labels` 同源。
- 同步 TypeScript contract、`robotControlSummary.test.ts` 和 `docs/product/pc_tools_workstation.md`。
- 该链路只读：刷新雷达 scan proof、读取雷达状态、刷新地图画面、刷新 summary，不启动雷达 lifecycle，不执行 Nav2/manual/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts`：1 个测试文件、10 个用例通过。
- `npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`：3 个测试文件、429 个用例通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `1357`。
- live smoke `GET http://127.0.0.1:7001/api/robot-control/summary` 读回：
  - `radar_overlay_status=not_current`
  - `radar_overlay_current_point_count=0`
  - `radar_overlay_source_point_count=156`
  - `radar_overlay_next_action_plain=旧雷达来源点 156 个已抑制；先刷新雷达扫描读数，再刷新地图画面，确认同轮雷达点贴图。`
  - `radar_overlay_refresh_sequence=["/api/robot-control/radar/scan-proof/refresh","/api/robot-control/radar/status","/api/robot-control/map/preview","/api/robot-control/summary"]`
  - `radar_overlay_refresh_sends_motion=false`
  - `radar_overlay_refresh_starts_radar_lifecycle=false`
  - `radar_overlay_blocks_free_move=false`
- 按声明 sequence 执行 no-motion 刷新后：
  - radar scan proof refresh 回包 `readback_only=true`、`no_motion_refresh=true`、`sends_motion_when_clicked=false`、`starts_radar_lifecycle=false`
  - map preview `radar_overlay_status=loaded`
  - map preview `radar_overlay_current_point_count=5`
  - summary `radar_overlay_status=loaded`
  - summary `radar_overlay_current_point_count=5`
  - summary `radar_map_points_visible=true`
  - summary `live_wysiwyg_missing_surface_ids=["camera"]`

## 剩余风险

- 本轮没有执行任何 motion/control POST；完整 Nav2 行程、PC 键盘连续手控和自由移动真实运动仍需现场安全确认后验收。
- 当前 WYSIWYG 只剩相机首帧缺口；相机仍需处理 USB full-speed/供电/线缆后复测。
