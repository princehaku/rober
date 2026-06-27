# PC free-roam stale 雷达障碍距离清理

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当 `lidar_fresh` gate 已降级为未刷新/stale/not fresh 时，`obstacle_clear` 里的旧“最近障碍 Xm”不再作为实时障碍距离展示。
  - `obstacle_clear` 会改为 `not_proven`，证据为“雷达未刷新，障碍距离不可用”。
- `pc-tools/workstation/test/catalog.test.ts`
  - 在 runtime 旧 gate + 雷达 stale readback 的合同测试里补充 `obstacle_clear` 清理断言。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 stale 雷达时旧障碍距离不可继续贴到普通首屏/地图。

## 验证结果

- `npm test -- --run catalog.test.ts -t "keeps stale radar readback in free-roam mapping gaps even when runtime gate is old-ready"`
  - 结果：通过，`1 passed | 123 skipped`。
- `npm test`
  - 结果：通过，`2 passed`，`288 passed`。
- `npm run build`
  - 结果：通过，生成 `dist/`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮 gate 文案。
- `curl -sS 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' | jq '{obstacle_gate: (.safe_command_boundary.free_roam_autonomy_gates[] | select(.id=="obstacle_clear")), lidar_gate: (.safe_command_boundary.free_roam_autonomy_gates[] | select(.id=="lidar_fresh")), mapping_missing: .readback_summary.free_roam.mapping_missing}'`
  - 结果：通过；`obstacle_clear.state=not_proven`，`evidence=雷达未刷新，障碍距离不可用`；`lidar_fresh.state=not_proven`，`mapping_missing=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`。

## 剩余风险

- 本轮不刷新真实雷达、不启动 free-roam、不发送任何运动控制；只是避免 stale 雷达距离被误读成实时障碍。
- live 当前雷达仍未 fresh，需要现场刷新雷达才能恢复真实障碍距离和建图验收。
