# 2026.07.02 24:45 `/map` ROS2 观察说明可见性

sprint_type: micro

## 实际改动

- 修复 `/map` 直达地图页默认 `observer` 模式下，通用 `.panel-note` 隐藏规则会把 `plain-map-ros2-tool-note` 一起隐藏的问题。
- 在直达地图页显式恢复 ROS2 观察折叠区显示，保证现场点击 `ROS2观察` 后能看到 RViz2 / Foxglove 只读观察说明。
- 同步更新 PC 工作站产品文档，明确该入口只用于工程观察，不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，也不发送任何运动控制。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts`（1 file / 237 tests passed）
- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm run build`（Vite 仅提示 chunk size warning）
- 通过：`cd pc-tools/workstation && npm run lint`

## 剩余风险

- 本轮只修复 PC 页面 CSS/DOM 合同，没有接真实 RViz2、Foxglove bridge、真实 `/map` 图像、雷达 scan 或真实小车运动接口做 HIL。
