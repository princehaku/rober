# PC map route target alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlMapPreviewResponse` 新增 `route_target` 顶层字段，作为既有 `target` 的同值别名；`readback_summary.map` 同步新增 `route_target` 对象。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：map preview 成功、失败兜底和 summary readback 都返回 `route_target`；当 route 来自 `path_preview_points` 时，目标点仍取同一份 map frame 路线的最后一个点，避免前端或脚本使用旧目标点。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：覆盖 `route_target === target`，并验证 summary 可直接读到目标点对象。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`：记录本轮地图目标点合同修正。

## 验证结果

- `npm test -- test/catalog.test.ts -t "map preview" --run`：通过，4 tests OK / 184 skipped。
- `npm test -- test/robotControlSummary.test.ts --run`：通过，15 tests OK。
- `npm test -- test/App.test.ts -t "map display|direct map|route goal|target|radar|keyboard|WASD|camera" --run`：通过，102 tests OK / 138 skipped。
- `npm run build`：通过，仅 Vite chunk size warning。
- 现场修复前 live 证据：`GET /api/robot-control/map/preview` 已有 `target={x:0.8,y:0.05,frame_id:map,source:path_preview_points,source_index:17}`、`route_target_visible=true`，但 `route_target=null`；本轮修复该别名缺口。

## 剩余风险

- 本轮只修 map preview/summary 目标点读回合同，不重新执行 Nav2 完整路线或 delivery success。
- 摄像头仍为 `/dev/video1` DV20 无首帧；该问题不影响地图目标点合同，但仍阻塞实时图传最终验收。
