# PC 首屏行程闭环入口仪表

sprint_type: micro

## 实际改动

- 普通首屏 `勾确认后可做` 区新增 `plain-trip-closure-gate` 只读仪表。
- 仪表把安全确认、图上路线 ready、执行按钮语义、同窗口轮速 L/R、送达 success 对齐状态和固定执行/送达 endpoint 放到首屏。
- 默认状态不出现 `Nav2`、`raw` 或 `/cmd_vel` 等工程词；已送达 fixture 下，首屏仪表能直接显示 `已闭环`。
- 同步更新 PC 工作站 README 和产品边界文档。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "marks the map goal as delivered only when delivery success matches the current Nav2 route"`，1 passed / 218 skipped。
- 通过：`npm test -- --run`，389 passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue newline warnings。
- 通过：`npm run build`，生成 `dist/assets/index-DJgw60-X.css` 和 `dist/assets/index-olr-X-VS.js`；仅 Vite chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮仅改 PC Web 只读仪表、DOM 合同和文档，不包含真实机器人 HIL、真实 Nav2 执行、真实 wheel L/R 上车采样或实机 delivery success 验证。
