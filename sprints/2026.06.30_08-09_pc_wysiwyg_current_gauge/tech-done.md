# PC WYSIWYG current gauge

sprint_type: micro

## 实际改动

- 在 PC 普通首屏 `当前所见` 区新增 `plain-wysiwyg-current-gauge`，把画面、地图、图上行程、小车位置和雷达贴图是否按当前事实显示合成一行只读仪表。
- 仪表 DOM 暴露 `data-camera-current-visible`、`data-map-current-visible`、`data-route-current-visible`、`data-robot-pose-visible`、`data-radar-map-points-visible`、雷达点/旧来源点计数、`data-old-radar-points-diagnostic-only`、`data-all-wysiwyg-ready`、下一步动作和固定只读 endpoint。
- 更新 PC 文档，明确该仪表不新增控制入口，固定 `data-sends-motion-when-clicked=false`。

## 验证结果

- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 passed / 218 skipped。
- `npm test -- --run`：通过，2 test files passed，389 tests passed。
- `npm run lint`：通过，0 errors；保留 4 个既有 Vue 换行 warning。
- `npm run build`：通过，Vite 输出 `dist/assets/index-jz2fMCMz.js` 和 `dist/assets/index-BFFGZWOb.css`；保留现有 chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮只验证 PC Web fixture 和 DOM 合同，不触发真实相机、雷达、地图刷新或小车运动。
- 两份历史 smoke artifact 在本轮开始前已是 dirty，本轮不纳入提交。
