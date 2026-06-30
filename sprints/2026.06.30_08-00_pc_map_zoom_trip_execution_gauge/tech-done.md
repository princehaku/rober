# PC map zoom and trip execution gauge

sprint_type: micro

## 实际改动

- 将 PC 普通首屏地图默认缩放从 `200%` 提升到 `300%`，保留 `适配` 回到 `100%`、最高 `400%`、全屏和观测模式；ROS2 配套继续标注 RViz2 / Foxglove，普通用户仍使用 PC 工作站地图。
- 新增 `plain-trip-execution-gauge` 行程仪表，把当前图上行程点数、主按钮是否会执行当前地图行程、托管 runtime、同窗口轮速 L/R、送达 success 是否对齐当前行程、固定执行/送达代理 endpoint 和下一步动作合成一行只读 DOM 合同。
- 顺手修复 `robotControlSummary.ts` 中一处正则字符类多余转义，解除 `npm run lint` 的既有硬错误；该修复不改变解析语义。
- 更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，记录地图放大、ROS2 配套工具边界和行程仪表验收口径。

## 验证结果

- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 passed / 218 skipped。
- `npm test -- --run test/App.test.ts -t "marks the map goal as delivered only when delivery success matches the current Nav2 route"`：通过，1 passed / 218 skipped。
- `npm test -- --run`：通过，2 test files passed，389 tests passed。
- `npm run build`：通过，Vite 输出 `dist/assets/index-CevzfbVX.js` 和 `dist/assets/index-CusXfb0q.css`；保留现有 chunk size warning。
- `npm run lint`：通过，0 errors；保留 4 个既有 Vue 换行 warning。
- `npm run build` 最终轮：通过，Vite 输出 `dist/assets/index-BJ7v8hxd.js` 和 `dist/assets/index-CusXfb0q.css`；保留现有 chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮只验证 PC Web fixture 和 DOM 合同，不触发真实小车运动，不代表真实 Nav2 HIL、真实轮速反馈或真实送达动作已通过。
- 两份历史 smoke artifact 在本轮开始前已是 dirty，本轮未纳入提交。
