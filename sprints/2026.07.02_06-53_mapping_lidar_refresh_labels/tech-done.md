# Mapping Lidar Refresh Labels

## sprint_type

micro

## 目标

- 修复 `GET /api/robot-control/summary` 顶层 `mapping_lidar_fresh_refresh_sequence` 只有 URL、没有中文 labels 的可读性缺口。
- 让现场脚本和普通首屏能直接显示“刷新雷达扫描读数 -> 读取雷达状态 -> 刷新总览”，明确这是 no-motion 建图雷达新鲜度复验链路。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `mapping_lidar_fresh_refresh_sequence_labels`，并与 `mapping_lidar_fresh_refresh_sequence` 同源透出到 `live_closure_summary` 和 summary 顶层。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐 `RobotControlLiveClosureSummary` 与 `RobotControlSummaryResponse` 类型。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加 labels 顺序和顶层/嵌套同源断言。
- `docs/product/pc_tools_workstation.md`
  - 同步建图雷达新鲜度复验 labels 合同。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`
  - 通过：`Test Files 3 passed (3)`、`Tests 428 passed (428)`。
- `npm run lint`
  - 通过。
- `git diff --check`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示既有 bundle 大小 warning。
- 重启 PC Node：
  - 通过；`node` 监听 `*:7001`。
- 只读 smoke：
  - `mapping_lidar_fresh_refresh_sequence_labels=["刷新雷达扫描读数","读取雷达状态","刷新总览"]`。
  - `labels_nested_same=true`、`sequence_nested_same=true`。
  - `sends_motion=false`、`starts_radar_lifecycle=false`、`blocks_free_move=false`。

## 剩余风险

- 本轮只补 no-motion 建图雷达新鲜度复验 labels，不执行雷达刷新、建图启动或真实自由移动；真实建图 ready 仍需要现场拿到相机首帧和雷达新鲜读回。
