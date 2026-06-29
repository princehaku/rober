# PC 共享 MJPEG 不随 WebRTC 关闭隐藏

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 中新增 `cameraMjpegSharedPreviewVisible`，让普通首屏 `<img data-testid="robot-camera-mjpeg-preview">` 使用独立的只读共享 MJPEG 可见条件。
- 保留 `cameraMjpegFallbackVisible` 作为状态文案条件，继续表达 WebRTC 自动连接是否被手动关闭抑制；这样“关闭画面”仍释放本页 WebRTC peer，但不会隐藏只读共享 MJPEG 预览入口。
- 在 `pc-tools/workstation/test/App.test.ts` 中新增源码契约测试，锁定 MJPEG `<img>` 不再复用 `previewAutoConnectSuppressed`。
- 更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，记录共享预览展示合同。

## 验证结果

- 已通过相机定向测试：`npm --prefix pc-tools/workstation test -- App.test.ts -t "shared MJPEG image|shared preview|MJPEG|mjpeg|camera"`，结果 `35 passed | 181 skipped`。
- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `381 passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，新 PID 为 `55023`。
- 已通过 7001 只读 summary / MJPEG status 验证：当前 live `viewer_count=0`、`upstream_connected=false`、`has_recent_frame=false`、`exclusive_camera_claim=false`、`source_diagnosis_status=uvc_no_frame_not_exclusive`，下一步白话为“检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。”

## 剩余风险

- 本轮只改 PC 浏览器展示条件，不调用 camera offer、camera probe、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 当前 live 相机仍是 UVC 无首帧；如果摄像头输入/供电未恢复，页面会继续显示真实失败并低频重试，而不会伪造画面可见。
