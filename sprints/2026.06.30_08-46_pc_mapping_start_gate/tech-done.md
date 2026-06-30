# PC 建图入口仪表

sprint_type: micro

## 实际改动

- 在普通首屏 `勾确认后可做` 区新增 `plain-mapping-start-gate` 建图入口仪表。
- 仪表把安全确认、画面首帧、雷达新鲜、建图记录是否可启动、自由移动主按钮是否会先建图再自由移动合成一行。
- DOM 合同暴露 `data-camera-ready-for-mapping`、`data-radar-ready-for-mapping`、`data-mapping-start-ready`、`data-primary-action-kind`、`data-primary-action-requests-mapping` 和固定建图/自由移动/地图预览 endpoint。
- 同步补充默认首屏和传感器 ready 后可启动建图的 Vitest 断言，并更新 PC README 与产品边界文档。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "shows start-ready free-roam autonomy as startable while runtime is still artifact-only"`，1 passed / 218 skipped。
- 通过：`npm test -- --run`，2 test files passed，389 tests passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue multiline warning。
- 通过：`npm run build`，生成 `dist/assets/index-5WKv-5pg.js` 和 `dist/assets/index-DtL5SpYN.css`；仅有 Vite chunk size warning。
- 通过：`git diff --check`，无 whitespace error。
- 已重启：`npm run api -- --host 0.0.0.0 --port 7001`，`node` PID `34272` 监听 `*:7001`，首页引用新 bundle `index-5WKv-5pg.js` / `index-DtL5SpYN.css`。

## 剩余风险

- 本轮只改 PC Web 只读仪表、DOM 合同和测试，不自动启动建图、不启动自由移动、不发送真实底盘或 Nav2 命令。
- 真实摄像头、真实雷达和真实建图记录仍需现场安全确认后做 HIL 验收。
