# PC 共享画面消费 camera health 首帧失败

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `共享画面` 状态在 MJPEG status 没有 `last_failure_reason` 时，会继续读取 Robot Control summary 的 camera health。
  - 当 camera health 已证明 `source_first_frame_failed` 且设备无人占用时，普通首屏显示“当前相机源没有输出首帧；设备没人占用，通常是 USB、摄像头输入或供电问题，不是浏览器独占”。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 MJPEG status 无最近失败、camera health 已证明首帧失败的回归测试，确认不触发 manual 或 free-roam start。
- `docs/product/pc_tools_workstation.md`
  - 同步记录共享画面 fallback 口径，避免 7001 重启后把 camera 无帧误显示成单纯等待视频边界。

## 验证结果

- `npm test -- --testNamePattern "shared camera preview state|camera health first-frame failure|live not-in-use camera"`：通过，3 passed。
- `npm test`：通过，2 test files / 258 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 该 sprint 只修 PC 画面状态解释，不修复真实 `/dev/video1` 首帧失败。
- 真实画面恢复仍需要现场检查 DV20 输入源、USB 线/供电、采集卡模式或替换 known-good UVC。
