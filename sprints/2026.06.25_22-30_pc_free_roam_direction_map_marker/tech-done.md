# PC free-roam direction map marker

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 为普通首屏地图增加扫地式建图手控方向 marker：地图记录中按住方向键/屏幕方向键时显示 `扫图方向：前进/左转/右转/后退`，松开后消失。
- 在 `pc-tools/workstation/src/styles.css` 增加方向 marker 样式，并按前进/后退/转向区分颜色。
- 在 `pc-tools/workstation/test/App.test.ts` 补充按住屏幕前进按钮时 marker 可见、松开后 marker 消失、且不误触 Nav2 execute 或 delivery complete 的断言。
- 更新 `docs/product/pc_tools_workstation.md`，记录方向 marker 的 UI 语义和控制边界。

## 验证结果

- 通过：`npm test -- --testNamePattern "keeps free-roam keyboard locked until map recording starts"`，1 passed / 169 skipped。
- 通过：`npm run lint`。
- 通过：`npm test`，170 passed。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 监听 `TCP *:7001`。
- 测试副作用：`npm test` 会刷新两个历史 smoke artifact 的 `checked_at`；已只还原这两个时间戳，未纳入本轮改动。

## 剩余风险

- 本轮是 PC 前端可视化与 mock 测试，不触发真实小车运动；真实 HIL 仍需 operator 在现场确认方向 marker 与机器人实际移动方向一致。
- 方向 marker 缺少 map-frame 位姿时固定在地图角落，只表达“当前按住方向”，不代表真实坐标。
