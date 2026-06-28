# PC Camera Status Next Action Alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `RobotControlCameraMjpegStatusResponse` 中新增顶层 `next_action_plain`。
- `pc-tools/workstation/src/server/index.ts`：让 `GET /api/robot-control/camera/mjpeg/status` 顶层 `next_action_plain` 对齐已有 `preview_next_action_plain`。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补 streaming、idle 和 source-first-frame-failed 三类状态的 alias 断言/fixture。
- `docs/product/pc_tools_workstation.md`：同步记录 camera MJPEG status 顶层下一步白话字段。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "camera MJPEG"`，9 个相关测试通过，151 个跳过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite 构建通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积提醒。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部通过。
- 通过：重启本机 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/camera/mjpeg/status`，live 返回 `status=source_first_frame_failed`，顶层 `next_action_plain=检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。`，并与 `preview_next_action_plain`、`camera_wysiwyg_next_action_plain` 一致。

## 剩余风险

- 本轮只修 PC 只读 camera status 字段，不改变 MJPEG relay 采集策略；live 仍显示 UVC 无首帧且非页面独占，现场需要检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。
