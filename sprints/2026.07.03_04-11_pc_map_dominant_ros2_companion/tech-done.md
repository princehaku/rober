# 2026.07.03 04:11 PC 地图主视图与 ROS2 配套答案

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`：扩大 PC 首页地图主视图的布局面积，工作站外壳从 `min(2800px, 100%)` 扩到 `min(3200px, 100%)`，visual-first 布局把地图列改成 `4fr`、右侧图传/WASD 窄栏保留为 `0.75fr`，首页地图卡和真实画布高度分别提升到更接近整屏。
- `pc-tools/README.md`：同步说明普通用户默认看 PC 首页和 `/map` 大屏；ROS2 配套是 RViz2 / Foxglove，分别用于本地工程调试和远程浏览器观察，不替代普通用户简易界面，不发送运动命令。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "map"`，结果 `1 passed`，`70 passed | 167 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`，结果 `2 passed`，`195 passed`。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 与 `vite build` 成功；仍有既有 large chunk warning，不影响本轮地图布局改动。

## 剩余风险

- 真实现场“是否足够大”仍受 PC 屏幕分辨率、浏览器缩放、地图源图尺寸影响；本轮只修正 UI 可见面积，不改变 `/map`、`/scan`、TF、Nav2 或地图数据质量。
