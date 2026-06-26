# PC 摄像头共享预览无首帧仍尝试接入

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将“WebRTC 自动接入 ready”和“MJPEG 共享预览可尝试”拆成两个 gate。
  - 当相机设备已加载或已选中 `/dev/video1`，即使上车 summary 报 `source_first_frame_failed`，普通首屏仍会挂载只读 `/api/robot-control/camera/mjpeg` 共享预览。
  - MJPEG 只有触发浏览器 `load` 后才算 `cameraMjpegFrameObserved`，因此该改动不会把无帧误报成“画面可见”或可建图。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 live 现场形态：`not_in_use + capture_read_returned_false` 时，页面仍显示共享 MJPEG 预览 URL，同时不发 WebRTC offer、不发底盘 manual、不启动 free-roam。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 PC 普通首屏的共享预览口径：后来进入的页面也会复用同一条 MJPEG 上游流，真实画面和真实失败都要所见即所得。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "live not-in-use camera first-frame failure"`
  - 通过：1 个相机无首帧/非独占用例通过。
- `cd pc-tools/workstation && npm test`
  - 通过：2 个测试文件，255 个用例通过。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
  - 仍有 Vite 既有 chunk 大小提示：`dist/assets/index-*.js` 超过 500 kB；不影响本轮改动。

## 剩余风险

- 本轮只改 PC 页面是否尝试共享 MJPEG，不修复真实 `/dev/video1` 无帧根因。
- 如果上车端 `/api/camera/mjpeg` 因摄像头硬件或 UVC 链路无帧返回 502/503，PC 会继续显示“不是独占，是无帧/后端不可用”，不会把它算作画面 ready。
- 建图 ready 仍必须等真实帧或样张证据；仅挂载共享 MJPEG 预览不等于 `camera_visible=true`。
