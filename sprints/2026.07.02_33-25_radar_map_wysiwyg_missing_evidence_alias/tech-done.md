# 雷达地图 WYSIWYG 缺口 alias

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 新增 `current_radar_map_wysiwyg_pack_missing_evidence` 与 `current_radar_map_wysiwyg_pack_missing_evidence_labels`。
- 雷达点已贴到当前地图时两个字段返回空数组；未贴到当前地图时分别返回 `radar_map_points` 和 `雷达地图标记`。
- 普通首屏 `plain-current-radar-map-wysiwyg-pack` 同步输出 `data-missing-evidence` 与 `data-missing-evidence-labels`，空数组显示为 `none`，方便 DOM smoke 和现场读回。
- 更新 PC 工作站产品文档，明确该 alias 只读，不启动雷达 lifecycle、Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `npm test -- test/App.test.ts -t "focuses field acceptance WYSIWYG refresh on camera only when radar and map are already visible"`：通过，`1 passed`。
- `npm test -- test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，`1 passed`。
- `npm test -- test/catalog.test.ts`：通过，`183 passed`。
- `npm run build`：通过，Vite 仅保留既有大 chunk 警告。
- `git diff --check`：通过。
- 已重启 PC 工作站到 `0.0.0.0:7001`，`curl http://127.0.0.1:7001/api/robot-control/summary` 只读读回：
  - `current_radar_map_wysiwyg_pack_status=loaded`
  - `current_radar_map_wysiwyg_pack_missing_evidence=[]`
  - `current_radar_map_wysiwyg_pack_missing_evidence_labels=[]`
  - `current_radar_map_wysiwyg_pack_blocks_wysiwyg=false`
  - `radar_overlay_wysiwyg_complete=true`
- `curl -I http://127.0.0.1:7001/map`：HTTP `200 OK`。

## 剩余风险

- 本轮只做 no-motion summary、DOM 与构建验证，没有发送任何运动控制命令。
- live summary 当前仍显示 `live_wysiwyg_missing_surface_ids=["camera"]`，相机首帧问题还需要现场换高速 USB/带供电 Hub 后复测。
- 真车 Nav2 行程、wheel raw L/R 非零、delivery success、PC 键盘连续手控和自由移动仍需要现场安全确认后的 HIL 验证。
- 工作区仍保留既有未纳入本轮的 artifact dirty 文件：
  - `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`
  - `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`
