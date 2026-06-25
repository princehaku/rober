# PC 实时画面等待绘帧 WYSIWYG

sprint_type: micro

## 目标

让普通首屏实时画面更严格地区分“WebRTC track 已到达”和“浏览器真的绘出了视频帧”，避免 operator 把连接态误读成已经能看到画面。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增本地 video 绘帧判断 `browserVideoFrameDrawn()`。
  - streaming 但 video 元素还没有可绘制帧时，首屏状态显示 `等待画面`，提示“视频已接入，等待浏览器绘出第一帧”。
  - 只有浏览器 video 元素已有尺寸/readyState 或 frame callback 证据后，才继续显示 `已打开`、`画面可见` 或 `画面偏暗`。
- `pc-tools/workstation/src/styles.css`
  - `等待画面` 状态使用连接中提示色。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 WebRTC track 已到达但 video 未绘帧的普通首屏测试。
  - 断言该状态不调用 camera probe、base manual 或其它控制动作。
- `docs/product/pc_tools_workstation.md`
  - 记录实时画面等待绘帧的 WYSIWYG 口径和安全边界。

## 验证结果

- `npm test -- -t "keeps camera preview in waiting state"`：通过，1 个定向用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 生产构建完成。
- `npm test`：通过，2 个测试文件、178 个用例全部通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 `node` 正在监听 `TCP *:7001`。

## 剩余风险

- 本轮是 PC 端 mock/DOM 单元验证；不等价于真实摄像头、真实 WebRTC 网络或现场光照质量 HIL。
