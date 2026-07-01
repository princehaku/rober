# PC 地图 ROS2 配套入口可见化

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将地图卡折叠入口从“工程观察”改为“工程观察：RViz2 / Foxglove”，让现场看到 ROS2 配套工具时不用猜入口含义。
  - 保持 `/map` 为普通用户首选 PC 内置地图大屏，默认 `1000%`、最高 `3200%`，地图、路线、小车位置和雷达点继续共用同一张 WYSIWYG 画布。
  - 该入口仍只读，保留 `data-starts-ros2=false`、`data-starts-rviz2=false`、`data-starts-foxglove=false`、`data-starts-nav2=false`、`data-sends-motion-when-clicked=false`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 同步 `map_display_engineering_tools_action_label` 为“工程观察：RViz2 / Foxglove”，避免 UI 与 summary API 口径不一致。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步只读合同字面量类型。
- `pc-tools/workstation/test/App.test.ts`
  - 更新地图卡 DOM 合同断言，覆盖新入口文案、`/map` 大屏、RViz2/Foxglove 分层和 no-motion 属性。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 更新 summary API 文案断言。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 catalog/live closure 文案断言。
- `pc-tools/README.md`
  - 追加 2026-07-01 22:20 CST 最新口径：普通用户用 `/map` PC 大地图；RViz2/Foxglove 是 ROS2 工程观察配套，不是发车前置。

## 验证结果

已运行：

```bash
$ cd pc-tools/workstation && npm test -- App.test.ts robotControlSummary.test.ts catalog.test.ts
Test Files  3 passed (3)
Tests  425 passed (425)

$ cd pc-tools/workstation && npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 1.47s

$ git diff --check
# 通过，无输出

$ HOST=0.0.0.0 PORT=7001 npm run api
# 重启后 lsof 显示 node 监听 TCP *:7001

$ curl -fsS 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787'
{
  "map_display_engineering_tools_action_label": "工程观察：RViz2 / Foxglove",
  "live_closure_summary.map_display_engineering_tools_action_label": "工程观察：RViz2 / Foxglove",
  "map_display_sends_motion_when_clicked": false,
  "map_display_starts_ros2": false,
  "map_display_starts_rviz2": false,
  "map_display_starts_foxglove": false,
  "map_display_starts_nav2": false
}
```

说明：`npm run build` 仍输出 Vite chunk size warning，这是当前单包体积提示，不影响本轮 TypeScript 合同、DOM 合同或打包通过。

## 剩余风险

- 本轮只改 PC 显示和只读 DOM/API 合同，不启动 RViz2/Foxglove/ROS2 runtime，不发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- `/map` 是否符合现场屏幕观感还需要真实现场屏幕查看；本轮测试和 7001 runtime readback 覆盖 DOM/API 合同和 no-motion 状态，不替代现场视觉验收。
