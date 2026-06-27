# PC camera known-good UVC next action

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏相机失败短提示新增 `cameraKnownGoodUvcSuffix()`，当上位机诊断给出 `check_usb_camera_input_power_or_known_good_uvc` 或 plain hint 已包含 known-good UVC 时，在 overlay / `画面状态` 保留“必要时换 known-good UVC 复测”。
  - 覆盖 `uvc_no_frame_not_exclusive`、backend smoke 无帧、not_in_use 无帧和读帧超时分支；只改变文案，不创建额外相机采集、不触发运动接口。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 live not-in-use camera first-frame failure 回归测试，验证普通首屏会把 known-good UVC 下一步显示出来，并继续隐藏 OpenCV/V4L2 长格式矩阵。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC 端相机失败短提示的新行为和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "explains a live not-in-use camera first-frame failure as not exclusive access"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 171 skipped (172)`
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`
  - `Tests 301 passed (301)`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - 仍有既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`git diff --check`

## 剩余风险

- 当前改动只修正 PC 可见排障口径；live 相机仍需要现场按提示检查 USB、摄像头输入、供电，或换 known-good UVC 复测。
- 未触发真实 camera reader、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；不构成 HIL 运动验证。
