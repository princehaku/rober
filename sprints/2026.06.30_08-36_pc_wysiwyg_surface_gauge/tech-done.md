# PC 实物所见仪表

sprint_type: micro

## 实际改动

- 在普通首屏 `当前所见` 区新增 `plain-wysiwyg-surface-gauge`，只按当前页面实际渲染出的共享画面帧、地图图像、图上行程层、小车位置和地图雷达点判断所见即所得。
- 新仪表暴露结构化 DOM 合同：`data-camera-frame-visible`、`data-map-image-visible`、`data-route-layer-visible`、`data-robot-marker-visible`、`data-radar-map-points-visible`、`data-radar-map-point-count`、`data-all-surfaces-visible` 和固定只读 endpoint。
- 同步补充默认首屏与雷达启动后地图点显示的 Vitest 断言，并更新 PC 工作站 README 和产品边界文档。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "auto-refreshes radar proof after plain radar start reports ok"`，1 passed / 218 skipped。
- 通过：`npm test -- --run`，2 test files passed，389 tests passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue multiline warning。
- 通过：`npm run build`，生成 `dist/assets/index-D8oDBzjB.js` 和 `dist/assets/index-tgqmkhTs.css`；仅有 Vite chunk size warning。
- 通过：`git diff --check`，无 whitespace error。
- 已重启：`npm run api -- --host 0.0.0.0 --port 7001`，`node` PID `8164` 监听 `*:7001`，首页引用新 bundle `index-D8oDBzjB.js` / `index-tgqmkhTs.css`。

## 剩余风险

- 本轮只改 PC Web 只读显示、DOM 合同和测试，不触发真实相机重启、雷达启动、地图刷新、底盘运动或 Nav2 执行。
- 未覆盖真实硬件 HIL；真实摄像头帧、真实雷达点贴图和真实 Nav2 路线仍需要现场安全确认后验证。
