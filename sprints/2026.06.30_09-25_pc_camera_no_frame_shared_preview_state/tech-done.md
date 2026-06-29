# PC 共享画面无首帧状态收紧

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增共享 MJPEG 已知不可用判断。页面仍自动接入共享 MJPEG `<img>`，但当 summary 或 MJPEG status 已证明 UVC 无首帧、上游 timeout 或 HTTP 502/503 时，实时画面卡业务状态直接显示失败原因，不再停留在“连接中”。
- `pc-tools/workstation/test/App.test.ts`：补强 live 形态测试，确认 `uvc_no_frame_not_exclusive` 时普通首屏显示“不是页面独占 / 没有取到视频帧”，同时仍保留共享 MJPEG `<img>`、共享预览链接，不调用 camera offer、manual、free-roam 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录共享预览状态口径。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "not-in-use camera first-frame failure|source usage is not loaded"`，2 个目标测试通过。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、381 个测试全部通过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript app/server 编译和 Vite build 通过；仅保留既有大 chunk 提示。
- 通过：`git diff --check`，未发现 whitespace/error。

## 剩余风险

- 这轮修正 PC 首屏对已知无帧的归因，不改变上位机 UVC 采集本身；真实画面仍需要现场检查 USB、摄像头输入、格式或供电，必要时换 known-good UVC 复测。
