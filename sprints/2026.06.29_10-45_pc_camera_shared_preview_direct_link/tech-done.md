# PC Camera Shared Preview Direct Link

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 的普通首屏实时画面卡片中新增“打开共享预览”链接。
  链接指向 PC Node `/api/robot-control/camera/mjpeg?baseUrl=...` 只读 relay，任何页面打开都会复用同一条上游 MJPEG 流。
- 新增 `robot-camera-shared-preview-link-summary` 说明行，直接显示“任何页面打开这个只读地址都会接入同一条上游流”和当前观看页面数。
- 在 `pc-tools/workstation/src/styles.css` 中为链接补齐按钮式样，保持普通用户简洁风格。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：
  `npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`
  - 结果：1 个文件通过，1 个测试通过，214 个跳过。
- 通过：
  `npm --prefix pc-tools/workstation test -- App.test.ts -t "explains a live not-in-use camera first-frame failure as not exclusive access"`
  - 结果：1 个文件通过，1 个测试通过，214 个跳过。
- 通过：
  `npm --prefix pc-tools/workstation test`
  - 结果：2 个文件通过，376 个测试通过。
- 通过：
  `npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript、Vite client build、server TypeScript 通过；仅保留既有 Vite chunk size warning。
- 通过 PC API 只读 live 验证：
  - `HOST=0.0.0.0 PORT=7001 npm --prefix pc-tools/workstation run api` 已启动，监听 PID `23492`。
  - `curl -fsS http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回共享预览事实：“谁打开页面都接入同一条上游流，当前 0 个页面观看”。
  - `GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status` 返回 `exclusive_camera_claim=false`、`viewer_count=0`、
    `upstream_connected=false`、`has_recent_frame=false`，继续归因为 UVC 无帧而不是页面独占。
  - live 验证只读 summary/health/status；未调用 manual、Nav2、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 剩余风险

- 真实 UVC 源当前仍未出帧；本轮只让共享预览入口更直接，不能替代现场检查 USB、摄像头输入、供电或 known-good UVC。
