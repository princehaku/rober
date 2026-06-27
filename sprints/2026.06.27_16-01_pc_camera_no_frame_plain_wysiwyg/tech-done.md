# 2026-06-27 16:01 PC camera no-frame plain WYSIWYG

## sprint_type

micro

## 设计

本轮推进“画面必须所见即所得”和 PC 端易用性。live 相机状态已经能证明不是页面独占：
`/dev/video1` 当前没人占用，MJPEG 共享预览支持多人接入，但 UVC 设备没有输出首帧。原首屏把同一条
无帧诊断和 MJPG/YUYV 格式尝试重复展示在 overlay、状态、共享状态和只读检查里，普通用户很难一眼判断。

设计口径：
- 当前事实条、画面 overlay 和 `画面状态` 只显示短结论。
- `只读检查` 保留完整格式尝试，便于排障。
- 共享预览仍明确“不是独占、多个页面共用同一条上游流”。
- 本轮只读页面状态，不启动相机探针、不触发 Nav2/manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `cameraSourcePlainFailureHint()` 改为短句，失败态首屏只说“不是页面独占、UVC 无帧、检查 USB/输入/供电”。
  - 新增 `cameraSourcePlainFailureDetailHint()`，把 `last_offer_format_attempts_summary` 只放到只读检查。
  - 相机失败态隐藏重复的通用 `panel-note`，避免 overlay 和 `画面状态` 之外再重复一遍。
  - 当前事实条去掉重复“不是独占”，显示 `USB Composite Device: DV20 USB 的 UVC 没有输出视频帧`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新相机无首帧、MJPEG shared preview、backend no-frame 等回归期望。
  - 锁定 overlay / `画面状态` 不再包含 `采集尝试`，只读检查仍保留长证据。
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录相机无首帧提示分层与共享预览非独占边界。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts -t "camera source|shared camera|MJPEG|first-frame|no-frame|plain first-screen hint"`
  - 结果：1 个 test file passed，15 tests passed，154 skipped。
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - 结果：2 个 test files passed，297 tests passed。
- 已通过：`npm --prefix pc-tools/workstation run build`
  - 结果：Vite build 成功，产物 `dist/assets/index-BBw2jtl2.js`；仍有 500 kB chunk size warning，非本轮新增失败。
- 已通过：`npm --prefix pc-tools/workstation run lint`
- 已通过：`git diff --check`
- 已重启 PC Node：`node` PID `80912` 监听 `*:7001`，HTML 引用新 bundle `index-BBw2jtl2.js`。
- live DOM 只读验证 `http://127.0.0.1:7001`：
  - 当前事实条：`USB Composite Device: DV20 USB 的 UVC 没有输出视频帧`
  - overlay：`不是页面独占：USB Composite Device: DV20 USB 没人占用，但 UVC 没有输出视频帧`
  - `robot-camera-wysiwyg-status` 不包含 `采集尝试`
  - `plain-camera-probe-summary` 仍包含 `采集尝试`
  - 未触发 manual、`/cmd_vel`、Nav2 execute、free-roam start、delivery complete 或 radar start。

## 剩余风险

- 本轮改善的是 PC 相机失败态展示；真实摄像头仍没有首帧，建图验收仍缺 `camera_first_frame`。
- 需要现场继续检查 USB、摄像头输入、供电或换 known-good UVC；没有把无帧状态误报成画面 ready。
- 完整 Nav2 路线执行、wheel raw L/R 非零、delivery success 和真实键盘连续运动还需要后续现场验证闭环。
