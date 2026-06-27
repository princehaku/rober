# 2026.06.28 05:25 PC camera cached frame WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `cameraMjpegCachedFramePending` 与 `plainCameraCachedFrameStatus`。
  - 当 PC Node 共享 MJPEG status 已读到 `upstream_active=true`、`content_type_loaded=true`、`cached_frame_loaded=true`，但当前页面还没完成 `<img>` load 时，普通首屏显示最近帧提示。
  - 该提示只消费只读 status，不新增 camera reader，不改变 camera ready gate，不发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 在共享 MJPEG 预览测试中覆盖“最近帧缓存先显示”的普通首屏文案，并继续断言不发送运动、自由移动或 Nav2 goal 请求。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC 共享画面最近帧提示的产品口径和安全边界。

## 验证结果

- `npm test -- --run test/App.test.ts -t "Camera Preview"`：通过，1 个测试文件通过，2 个测试通过，190 个跳过。
- `npm test`：通过，2 个测试文件通过，339 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；仍有既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮只改善“谁进入页面都能看到已有共享画面证据”的 PC WYSIWYG 提示，不修复真实 UVC 无首帧问题。
- 真实上位机当前仍需现场继续验证摄像头出帧、雷达运行、Nav2 lifecycle 和安全确认后的完整路线执行。
