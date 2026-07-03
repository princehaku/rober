# PC 地图直达页视口修正

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/styles.css`：把 `/map` 直达页的 `.plain-map-layer` 从通用 fullscreen 最小高度里摘出来，改为跟随可见 map viewport 的 `height: 100%` / `min-height: 0`；同时在 `/map` 隐藏普通首页才需要的 caption 和雷达证明行。这样 `/map` 进入后是一块视口内的大地图工作区，缩放仍由现有 100% 细节视角、45% 适配和 1200% 最大放大控制。
- `pc-tools/workstation/test/App.test.ts`：更新样式合同断言，防止 `/map` 再被通用 `1040px` 最小高度撑出屏幕。
- `docs/product/pc_free_roam_mapping_design.md`：同步说明 `/map` 直达页的画布高度边界。

## 验证结果

- 通过：`npm test -- App.test.ts`，1 个测试文件、239 个测试通过。
- 通过：`npm run build`，`tsc`、Vite production build 和 server `tsc` 均通过；Vite 仍提示既有 JS chunk 超过 500 kB。
- 通过：本机浏览器打开 `http://127.0.0.1:7001/map?layout_check=1783073240`，新 CSS 资产为
  `index-UO3jvBjl.css`；`.plain-map-layer` 高度 `667px`，等于 `.plain-map-viewport` 高度 `667px`，
  `min-height=0px`；caption 和雷达证明行均为 `display:none`；地图图像、图上行程、目标点、小车位置和雷达点均显示在同一画布。

## 剩余风险

- 该改动只影响 PC 地图直达页的布局，不改变 ROS2、Nav2、建图、底盘手控、相机或雷达接口。
