# Stopped Radar Overlay 不当作当前地图点

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `mapSummaryFromReadbacks()` 中把 `lidar.lifecycle_state === "stopped"` 也视为雷达已停。
  - 当旧 scan proof 仍有点、但 runtime `/scan` stale 且 lifecycle stopped 时，地图 overlay 降级为 `not_current`，当前 overlay 点数为 `0`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 将 stale stopped radar proof 测试改成当前 live 形态：只提供 `lifecycle_state=stopped`，不提供 `lifecycle_running=false`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 stopped/stale 雷达点只可作为历史材料，不能作为当前地图 overlay。

## 验证结果

- 已通过 focused radar overlay 测试：
  - `npm test -- --testNamePattern "radar overlay|Radar overlay|stale stopped|not-current|雷达" --maxWorkers=1 --no-fileParallelism`
  - 结果：7 passed。
- 已做 7001 只读复验：
  - 当前运行中的 7001 仍返回旧口径 `radar_overlay_status=partial`、`radar_overlay_scan_preview_point_count=65`。
  - 结论：现场 Node 进程尚未加载本轮源码改动；需重启/热更新 PC Node 后新 summary 口径才会生效。
- 已通过 PC workstation 全量测试：
  - `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 结果：329 passed。
- 已通过静态和构建验证：
  - `npm run lint`
  - `npm run build`
  - `git diff --check`
  - `npm run build` 仍有既有 Vite chunk size warning，不影响构建通过。

## 剩余风险

- 本轮只修 summary 只读口径，不启动雷达、不刷新地图、不发送真实运动命令。
- 现场仍需启动/刷新雷达并读到 fresh scan 后，地图才能显示当前雷达局部轮廓或贴图点。
- 当前 7001 运行进程未重启前，现场 API 仍会显示旧 `partial` 口径。
