# PC camera frame truth

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 为普通首屏实时画面增加浏览器绘帧口径，把 `videoElementFrameStatus` 翻译为普通用户可理解的“已绘制视频帧 / 等待可绘制帧 / 未绑定实时流”。
- `画面可见` 和 `画面偏暗` 状态会同步显示本页 video 元素帧尺寸，例如 `浏览器已绘制视频帧 640x480`，避免把连接成功误读成画面真的可见。
- 在 `pc-tools/workstation/test/App.test.ts` 更新可见帧和偏暗帧断言，覆盖普通首屏画面 WYSIWYG 文案。
- 更新 `docs/product/pc_tools_workstation.md` 记录该状态只读本地 video 元素诊断，不触发控制动作。

## 验证结果

- 通过：`npm test -- --testNamePattern "shows real RTC preview frame quality in the plain first screen|marks near-black preview as 画面偏暗 instead of optimistic 已打开"`，1 passed / 170 skipped。
- 通过：`npm test -- --testNamePattern "marks near-black preview as"`，1 passed / 170 skipped。
- 通过：`npm run lint`。
- 通过：`npm test`，171 passed。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 监听 `TCP *:7001`。
- 测试副作用：`npm test` 刷新两个历史 smoke artifact 的 `checked_at`；已只还原这两个时间戳，未纳入本轮改动。

## 剩余风险

- 本轮验证使用浏览器 DOM/mock WebRTC，不代表真实现场摄像头链路已稳定；真实画面仍需上车 HIL 和 operator 目视确认。
- 当前普通文案只显示绘帧状态和尺寸，不展示高级诊断字段；细节仍在折叠区。
