# PC 雷达 stale 原因所见即所得

## sprint_type

micro

## 背景

- live 7001 summary 显示 `latest_scan_status=latest_proof_stale_while_lifecycle_running`，LiDAR lifecycle 已运行但 scan proof 过期。
- 原普通首屏会把 lifecycle running 但 proof 未 fresh 的状态统一显示成“最新记录不完整”，对 stale 现场不够准确。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainRadarRefreshReason`，按 `continuous_scan_status/continuity_window_status` 区分 stale、incomplete 和连续窗口未读到。
  - `雷达待刷新` hint 中 stale 显示 `最新记录已过期`，incomplete 保持 `最新记录不完整`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `shows stale running lidar proof as expired instead of incomplete`，覆盖 live 同款 stale 状态。
  - 断言点击仍只调用固定 radar proof refresh，不调用 radar start、Nav2 execute、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 stale/incomplete 的普通首屏口径和安全边界。

## 验证结果

- `npm test -- -t "stale running lidar|running lidar proof|plain radar"`：通过，1 个 test file，6 passed，204 skipped。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 保留既有 `Some chunks are larger than 500 kB` warning。
- `npm test`：通过，2 个 test file，210 passed。
- 全量测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，已用精确 patch 恢复，避免把测试副作用纳入本轮提交。

## 剩余风险

- 本轮是 PC 首屏状态文案和 mock 单元验证，未做真实 LiDAR HIL。
- stale/incomplete 仍都保持 `雷达待刷新`，不会自动启动雷达或提升 safe_to_control；现场仍需点击 `刷新雷达` 取新 proof。
