# PC 顶层安全确认入口

sprint_type: micro

## 实际改动

- 在普通首屏 `勾确认后可做` 区新增 `plain-unified-safety-gate` / `plain-unified-safety-confirm` 顶层安全确认入口。
- 顶层确认直接复用 `plainUnifiedSafetyConfirmed`，勾一次会同步行程、自由移动、移动面板和高级确认框；确认本身不发送任何控制请求。
- DOM 合同明确：发车前最小预检只需现场安全确认，相机、雷达和 operator report 不作为普通低速运动额外门槛。
- 同步补充 Vitest 断言、PC README 和产品边界文档。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "reuses one plain safety confirmation for trip, keyboard, and free-roam mapping"`，1 passed / 218 skipped。
- 通过：`npm test -- --run`，2 test files passed，389 tests passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue multiline warning。
- 通过：`npm run build`，生成 `dist/assets/index-DPIx_Eh2.js` 和 `dist/assets/index-BS9gnBcH.css`；仅有 Vite chunk size warning。
- 通过：`git diff --check`，无 whitespace error。
- 已重启：`npm run api -- --host 0.0.0.0 --port 7001`，`node` PID `19378` 监听 `*:7001`，首页引用新 bundle `index-DPIx_Eh2.js` / `index-BS9gnBcH.css`。

## 剩余风险

- 本轮只改 PC Web 前端确认入口、DOM 合同和测试，不发送真实底盘、Nav2、键盘或自由移动命令。
- 真实 HIL 仍需现场安全确认后验证；本轮证明的是 UI 入口和前端门禁同步，不等同于真实底盘运动已验收。
