# PC 雷达距离读数非地图点所见即所得

sprint_type: micro

## 实际改动

- 更新 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当机器人 map pose 已读到、雷达运行但没有 `scan_preview_points` 点数组，且只读到最近障碍距离时，地图 marker 显示 `雷达距离：...（非地图点）`，aria 明确这是距离读数，不是已贴到地图的雷达点。
- 更新 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：雷达 freshness 与坐标口径在 pose 已有但缺点数组时，不再提示“等定位”，而是说明“没有点数组，未贴到地图”。
- 更新 `pc-tools/workstation/test/App.test.ts`：新增有 map pose、雷达运行、点数组为 0、仅有最近障碍距离的 live 形状测试，并继续断言不调用 radar start、base/manual、Nav2 execute 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md`：同步记录雷达 scalar distance 不能冒充地图点的产品口径。

## 验证结果

- 通过：`npm test -- App.test.ts --testNamePattern "radar|雷达|obstacle-only"`；结果 `1 passed`，`23 passed | 141 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅有既有 Vite chunk size warning。
- 通过：`npm test`；结果 `2 passed`，`285 passed`。
- 通过：`git diff --check`。
- live 只读事实：`/api/robot-control/summary` 当前显示雷达 lifecycle running、raw packet true、`scan_preview_point_count=0`，同时 free-roam gate 有最近障碍距离；本轮 UI 分支正针对该形状。

## 剩余风险

- 本轮没有刷新真实雷达 proof，也没有启动/停止雷达；只修 PC 地图对既有只读摘要的表达。
- 如果上车端继续不返回 `scan_preview_points`，地图仍不会画真实雷达点，只显示距离读数和非地图点说明。
- 完整 Nav2 同窗口 wheel raw L/R 非零、delivery success、真实 free-roam 运动仍未在本轮验证。
