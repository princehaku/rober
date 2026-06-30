# PC 键盘入口仪表

sprint_type: micro

## 实际改动

- 在普通首屏 `勾确认后可做` 区新增 `plain-keyboard-hold-gate` 键盘入口仪表。
- 仪表明确：点击启用键盘不发车，只有按住方向键/WASD 才连续发送低速 pulse，松开/失焦后必须 stop 收口。
- DOM 合同暴露 `data-arm-sends-motion=false`、`data-requires-hold-to-move=true`、`data-sends-motion-while-held`、连续 pulse 计数、pulse 间隔/时长、stop 收口要求和固定 manual/stop endpoint。
- 同步补充默认首屏、键盘启用、按住中和验证完成的 Vitest 断言，并更新 PC README 与产品边界文档。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "enables non-stop motion only after complete operator material and still uses the fixed workstation proxy"`，1 passed / 218 skipped。
- 通过：`npm test -- --run`，2 test files passed，389 tests passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue multiline warning。
- 通过：`npm run build`，生成 `dist/assets/index-BPdNRqZ0.js` 和 `dist/assets/index-DXz9y0Fs.css`；仅有 Vite chunk size warning。
- 通过：`git diff --check`，无 whitespace error。
- 已重启：`npm run api -- --host 0.0.0.0 --port 7001`，`node` PID `51110` 监听 `*:7001`，首页引用新 bundle `index-BPdNRqZ0.js` / `index-DXz9y0Fs.css`。

## 剩余风险

- 本轮只改 PC Web 只读仪表、DOM 合同和测试，不自动启用键盘、不发送真实 manual/stop 或底盘命令。
- 真实键盘手控和真实轮速仍需现场安全确认后做 HIL 验收。
