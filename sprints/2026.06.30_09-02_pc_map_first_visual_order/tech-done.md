# PC 地图优先视觉顺序

sprint_type: micro

## 实际改动

- 普通首屏 `visual-first` 布局中，地图卡新增 `data-visual-priority=pc-primary-map-first`。
- CSS 视觉顺序调整为地图先占整行，实时画面和雷达卡跟随显示；地图仍保持默认大图、300% 缩放、全屏和观测模式。
- PC 文档同步说明：RViz2/Foxglove 是 ROS2 工程调试配套，普通用户主入口仍是简易 PC 工作站大地图。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，1 passed / 218 skipped。
- 通过：`npm test -- --run`，389 passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue newline warnings。
- 通过：`npm run build`，生成 `dist/assets/index-D3EP0Ndz.css` 和 `dist/assets/index-DxwKdGXo.js`；仅 Vite chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮仅改 PC Web 布局和 DOM 合同，不包含真实机器人 HIL、RViz2 启动验证或摄像头/雷达实机画面验证。
