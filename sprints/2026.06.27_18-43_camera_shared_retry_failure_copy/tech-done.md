# 共享画面失败态自动重试提示

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 共享 MJPEG 失败文案在 `camera_source_first_frame_failed`、`camera_mjpeg_upstream_timeout`、HTTP 502/503 和 health-only 首帧失败时，补充 `页面会低频自动重试`。
  - 仍保留“不是独占 / UVC 无帧 / 上游无画面”的 WYSIWYG 归因，不把无首帧说成页面加载中或浏览器独占。
- `pc-tools/workstation/test/App.test.ts`
  - 更新共享预览失败态回归：summary fallback、MJPEG status、upstream timeout 和 HTTP 503 都必须展示自动重试提示，且不暴露内部 token、不发送运动请求。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 2026-06-27 18:43 口径：失败态也要告诉普通用户页面会低频自动重连同一条只读共享 relay。

## 验证结果

- 已通过：`npm test -- --run test/App.test.ts -t "shared camera|shared MJPEG|shared preview|not-in-use camera"`，7 passed / 167 skipped。
- 已通过：`npm test -- --run`，2 test files passed，303 tests passed。
- 已通过：`npm run build`。Vite 仍输出既有 chunk >500 kB 警告，不影响本轮通过。
- 已通过：`npm run lint`。
- 已通过：`git diff --check`。

## 剩余风险

- 本轮只改 PC WYSIWYG 文案和回归测试，没有修复真实 DV20/UVC 首帧超时。live 仍需要检查 USB、摄像头输入、供电或换 known-good UVC。
- 本轮未触发 camera offer、manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
