# PC 移动总仪表

sprint_type: micro

## 实际改动

- 在普通首屏 `勾确认后可做` 区新增 `plain-motion-readiness-gauge`，把安全确认、图上行程、键盘连续手控、自由移动和相机/雷达是否阻止先动合成一行普通用户可读状态。
- 新仪表暴露结构化 DOM 合同：最小预检只需安全确认、图上行程是否 ready/会不会发车、键盘是否按住才发连续 pulse、最佳连续 pulse 数、自由移动是否可启动、相机/雷达是否阻止先动、固定行程/键盘/自由移动 endpoint。
- 同步补充 PC 工作站 README、产品边界文档和 Vitest 断言，保持 PC 简易界面文档与实现一致。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "allows free-roam recording when camera source is selected but not yet frame-proven"`，1 passed / 218 skipped。
- 通过：`npm test -- --run`，2 test files passed，389 tests passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue multiline warning。
- 通过：`npm run build`，生成 `dist/assets/index-yMSFV6Ae.js` 和 `dist/assets/index-DknmGUnf.css`；仅有 Vite chunk size warning。
- 通过：`git diff --check`，无 whitespace error。
- 已重启：`npm run api -- --host 0.0.0.0 --port 7001`，`node` PID `92972` 监听 `*:7001`，首页引用新 bundle `index-yMSFV6Ae.js` / `index-DknmGUnf.css`。

## 剩余风险

- 本轮只改 PC Web 只读显示、DOM 合同和测试，不发送真实底盘、Nav2、键盘或自由移动命令。
- 未覆盖真实上位机 HIL、真实摄像头画面、真实雷达贴图和真实 Nav2 行程执行；这些仍需要现场安全确认后另行验收。
