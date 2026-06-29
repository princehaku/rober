# PC 画面媒体元素 DOM 合同

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间: 2026-06-30 18:25 CST

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `robot-camera-mjpeg-preview` 共享 MJPEG `<img>` 新增当前帧可见、MJPEG 帧可见、共享流状态来源、观看人数、上游连接、视频边界、缓存帧、非独占、共享采集、单上游、自动接入和固定 MJPEG/status 入口 DOM 证据。
  - `robot-camera-preview-video` WebRTC `<video>` 新增当前帧可见、视频帧可见、非独占、单上游和固定共享入口 DOM 证据。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 MJPEG load 后的 WYSIWYG 测试，证明实际 `<img>` 元素自身暴露共享单上游、固定入口和当前帧可见。
  - 扩展 WebRTC 绘帧测试，证明实际 `<video>` 元素自身暴露当前视频帧可见、固定共享入口和非独占/单上游合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 记录 2026-06-30 18:25 CST 的画面媒体元素 DOM 合同。

## 验证结果

- 已通过:
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "keeps shared MJPEG image independent from WebRTC auto-connect suppression"`
  - `cd pc-tools/workstation && npm test -- test/App.test.ts -t "starts and stops Camera Preview through workstation camera proxy while keeping control locked"`
  - `cd pc-tools/workstation && npm run build`
    - 结果: TypeScript 与 Vite build 通过，生成 `dist/assets/index-RQswcyAo.js` 和 `dist/assets/index-BZI7zFw0.css`
  - `cd pc-tools/workstation && npm test -- --run`
    - 结果: `Test Files 2 passed (2)`, `Tests 389 passed (389)`
  - `git diff --check`
    - 结果: 通过，无 whitespace error
  - 重启并验证 `0.0.0.0:7001`
    - 结果: `node` 监听 `TCP *:7001`
  - `curl -fsS http://127.0.0.1:7001/`
    - 结果: 返回 `Rober PC Tools Workstation`，资产为 `index-RQswcyAo.js` / `index-BZI7zFw0.css`
  - `curl -fsS http://127.0.0.1:7001/assets/index-RQswcyAo.js | rg ...`
    - 结果: 构建产物包含 `data-current-mjpeg-frame-visible`、`data-current-video-frame-visible`、`data-shared-preview-status-source`、`data-shared-preview-exclusive-camera-claim`、`data-shared-preview-shared-capture`、`data-fixed-shared-preview-endpoint`、`data-fixed-shared-preview-status-endpoint`
  - `GET http://127.0.0.1:7001/api/robot-control/summary`
    - 结果: HTTP 200，`schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，相机 summary 返回 `shared_preview_shared_capture=true`、`shared_preview_exclusive_camera_claim=false`

## 剩余风险

- 本轮只补 PC 普通首屏实际媒体元素 DOM 合同和前端测试；没有接真实摄像头做浏览器画面 HIL 验证。
- 旧 artifact 文件仍有历史未提交改动，本轮不纳入提交范围。
