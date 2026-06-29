# PC free-roam start-ready 别名统一

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 为 summary free-roam readback 与 latest proxy 补齐 `free_roam_motion_start_ready/free_roam_motion_ready/free_roam_mapping_ready/free_roam_mapping_missing_reasons` 等别名。
- `pc-tools/workstation/src/server/index.ts`
  - `GET /api/robot-control/free-roam/autonomy/latest` 返回 `free_move_ready/free_roam_motion_start_ready/free_roam_motion_ready/free_roam_mapping_ready/free_roam_mapping_missing_reasons/mapping_ready/mapping_missing_reasons`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.free_roam` 同步返回同名字符串别名，让 summary 与 latest 字段口径一致。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补充 summary exact contract 和 latest proxy 断言，防止脚本读到空字段。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 start-ready 与 runtime-ready 的语义差异。

## 验证结果

- `npm run build`：通过。
- `npm test -- catalog.test.ts`：通过，`166 passed`。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`。
- live `curl http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/latest`：
  - `proxy_status=latest_loaded`
  - `free_roam_motion_start_ready=true`
  - `free_roam_motion_ready=false`
  - `free_roam_mapping_ready=false`
  - `mapping_ready=false`
  - `free_roam_mapping_missing_reasons=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`
  - `sends_motion_commands=false`
- live `curl http://127.0.0.1:7001/api/robot-control/summary`：
  - `readback_summary.free_roam.free_roam_motion_start_ready=true`
  - `readback_summary.free_roam.free_roam_motion_ready=false`
  - `readback_summary.free_roam.free_roam_mapping_ready=false`
  - `readback_summary.free_roam.mapping_ready=false`
  - `motion_runtime_status_plain=当前未在自由移动运行态；motion_ready=false 只表示尚未开始发布运动，不是启动阻塞。`

## 剩余风险

- 本轮只补只读字段别名，不启动自由移动、不启动建图、不发送真实运动命令。
- 当前 live 自由移动仍需要现场安全确认后点击开始，才能进入运行态并观察 wheel/地图材料。
