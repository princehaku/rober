# PC 地图雷达 0 点 marker 所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图雷达 marker 增加 0 点分支：雷达运行但没有可显示 scan 点时，marker 直接显示 `暂无地图点`。
  - raw packet 已观察但 scan 点为 0 时，marker 显示 `原始包已收到，暂无地图点`。
  - 雷达未运行且没有最近点时，marker 显示 `地图0点`，避免现场误以为地图漏刷新。
- `pc-tools/workstation/test/App.test.ts`
  - 增加有 map-frame 位姿但雷达 0 点的回归测试，确认 marker、aria、雷达点 SVG 都按真实状态显示。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC 地图雷达 marker 的所见即所得口径。

## 验证结果

- `npm test -- --run test/App.test.ts`
  - 通过：`Test Files 1 passed (1)`，`Tests 151 passed (151)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
  - Vite 仍提示产物 chunk 大于 500 kB，这是既有打包体积提示，不影响本轮功能。
- PC Node 已重启到 `0.0.0.0:7001`，`node` 监听 `*:7001`，screen 会话为 `rober_pc_7001`。
- 只读 live summary 复核：
  - `readback_summary.lidar.lifecycle_running=false`
  - `readback_summary.lidar.scan_preview_point_count=0`
  - `o3_proof_summary.scan_preview_points=[]`
  - `map_preview` 为空。

## 剩余风险

- 本轮只做 PC UI/DOM 回归，不执行真实雷达启动、Nav2 路线或底盘运动。
- 真实 live 当前 summary 仍显示雷达未运行、地图 preview 为空；这不是本轮 UI 修正能证明的硬件/ROS 雷达点恢复。
